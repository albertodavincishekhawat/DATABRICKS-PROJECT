# Lambda Deployment Guide - RBI Data Downloader

## Overview

Two Lambda functions work together:
1. **RBI Downloader Lambda** - Downloads RBI balance sheet, saves to S3 (runs weekly)
2. **Main Data Collection Lambda** - Pulls data from YFinance + S3 + scrapers (runs daily)

## Step 1: Setup S3 Bucket

```bash
# Create S3 bucket for data storage
aws s3 mb s3://my-portfolio-data --region us-east-1

# Create folders
aws s3api put-object --bucket my-portfolio-data --key data/
aws s3api put-object --bucket my-portfolio-data --key backups/
```

## Step 2: Create RBI Downloader Lambda Layer (with Selenium + ChromeDriver)

This is the complex part - we need Chrome and ChromeDriver in a Lambda layer.

### Option A: Use Pre-built Layer (Easiest)

Use a community-maintained layer that includes Chrome + ChromeDriver:

```bash
# For Python 3.11, us-east-1
# ARN: arn:aws:lambda:us-east-1:496032497324:layer:Selenium-py311:1

# Check available layers:
# https://github.com/serverless-chrome/serverless-chrome/wiki/Advanced-usage#pre-built-aws-lambda-layers
```

### Option B: Build Custom Layer (Advanced)

If Option A doesn't work for your region:

```bash
# Create layer directory
mkdir -p python/lib/python3.11/site-packages
cd python/lib/python3.11/site-packages

# Install dependencies
pip install selenium -t .

# Download ChromeDriver for Lambda
# Get latest from: https://googlechromelabs.github.io/chrome-for-testing/
# Lambda needs: linux/x64 version

# Copy Chrome binary to layer
mkdir -p ../../opt/chrome
cp chrome ../../opt/chrome/
cp chromedriver ../../opt/chromedriver

# Create layer ZIP
cd /path/to/python/..
zip -r ../selenium-layer.zip .

# Upload to Lambda
aws lambda publish-layer-version \
  --layer-name selenium-chrome \
  --zip-file fileb://../selenium-layer.zip \
  --compatible-runtimes python3.11
```

## Step 3: Deploy RBI Downloader Lambda

```bash
# 1. Create Lambda function
aws lambda create-function \
  --function-name rbi-balance-sheet-downloader \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-s3-access \
  --handler rbi_downloader_lambda.lambda_handler \
  --zip-file fileb://rbi_downloader_lambda.zip \
  --timeout 120 \
  --memory-size 1024 \
  --environment Variables={RBI_S3_BUCKET=my-portfolio-data,RBI_S3_KEY=data/rbi_balance_sheet.csv}

# 2. Attach Selenium layer
aws lambda update-function-configuration \
  --function-name rbi-balance-sheet-downloader \
  --layers arn:aws:lambda:us-east-1:496032497324:layer:Selenium-py311:1

# 3. Create IAM role for S3 access
cat > lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name lambda-s3-access \
  --assume-role-policy-document file://lambda-trust-policy.json

# 4. Add S3 permissions
aws iam put-role-policy \
  --role-name lambda-s3-access \
  --policy-name s3-write \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "s3:PutObject",
        "Resource": "arn:aws:s3:::my-portfolio-data/data/*"
      }
    ]
  }'
```

## Step 4: Schedule Lambda with CloudWatch Events

```bash
# Create EventBridge rule (weekly, Friday 2 PM UTC)
aws events put-rule \
  --name rbi-data-download-schedule \
  --schedule-expression "cron(0 14 ? * FRI *)"

# Target the Lambda function
aws events put-targets \
  --rule rbi-data-download-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:rbi-balance-sheet-downloader"

# Grant permission for EventBridge to invoke Lambda
aws lambda add-permission \
  --function-name rbi-balance-sheet-downloader \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT:rule/rbi-data-download-schedule
```

## Step 5: Test the RBI Downloader

```bash
# Test locally
python3 src/lambda_functions/rbi_downloader_lambda.py

# Test in Lambda
aws lambda invoke \
  --function-name rbi-balance-sheet-downloader \
  --payload '{"test_mode": true}' \
  response.json

cat response.json
```

## Step 6: Deploy Main Data Collection Lambda

```bash
# Create Lambda for main data collection
# This function will:
# 1. Fetch YFinance data
# 2. Fetch RBI data from S3
# 3. Run all 4 scrapers
# 4. Save combined data to S3

aws lambda create-function \
  --function-name portfolio-data-collector \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-s3-access \
  --handler data_collector_lambda.lambda_handler \
  --zip-file fileb://data_collector_lambda.zip \
  --timeout 300 \
  --memory-size 2048 \
  --environment Variables={RBI_S3_BUCKET=my-portfolio-data,DATA_OUTPUT_BUCKET=my-portfolio-data}

# Schedule daily (6 PM UTC = after market close in India)
aws events put-rule \
  --name portfolio-data-daily \
  --schedule-expression "cron(0 18 ? * MON-FRI *)"

aws events put-targets \
  --rule portfolio-data-daily \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:portfolio-data-collector"
```

## Step 7: Monitor Lambda Executions

```bash
# View CloudWatch Logs
aws logs tail /aws/lambda/rbi-balance-sheet-downloader --follow

# Get Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=rbi-balance-sheet-downloader \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 86400 \
  --statistics Average,Maximum
```

## Environment Variables (Lambda)

Set these in Lambda console or via AWS CLI:

```
RBI_S3_BUCKET=my-portfolio-data
RBI_S3_KEY=data/rbi_balance_sheet.csv
DATA_OUTPUT_BUCKET=my-portfolio-data
MOSPI_API_TOKEN=your_token_here  # Optional
```

## Troubleshooting

### Lambda Timeout
- Increase timeout from 120s to 300s
- Selenium + Chrome can be slow

### Out of Memory
- Increase memory from 1024 MB to 2048 MB
- Selenium needs memory for browser

### Selenium Not Found
- Verify layer is attached
- Check layer ARN matches your region
- Build custom layer if needed

### S3 Access Denied
- Verify IAM role has S3 permissions
- Check bucket name and key in environment variables
- Ensure S3 bucket exists

## Cost Estimate

- RBI Downloader: ~$0.50/month (1 invocation/week, 120s @ 1GB)
- Data Collector: ~$5-10/month (daily, 5 seconds @ 2GB)
- S3 Storage: ~$1/month (10 GB)
- Total: ~$6-12/month for full automation

## Testing Checklist

- [ ] RBI Lambda downloads and saves to S3
- [ ] Data Collector Lambda reads from S3
- [ ] CloudWatch logs show successful executions
- [ ] S3 files have correct data
- [ ] Scheduled executions run on time
- [ ] Errors trigger CloudWatch alarms

## Next Steps

1. Deploy RBI Downloader → Verify S3 file created
2. Deploy Data Collector → Verify combined data in S3
3. Connect Phase 3 pipeline to read from S3
4. Set up CloudWatch alarms for failures
