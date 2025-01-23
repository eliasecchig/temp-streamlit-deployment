# Deploy Streamlit App to Cloud Run

This guide outlines the steps to deploy your Streamlit application to Cloud Run and configure Identity-Aware Proxy (IAP) for secure access.

## Prerequisites

Before you begin, ensure you have the following:

-   A Google Cloud project with billing enabled.
-   The Google Cloud SDK installed and configured.
-   A Streamlit application ready for deployment.

## Deployment Steps

### 1. Set Environment Variables

First, set the following environment variables:

```bash
export PROJECT_ID=genai-blackbelt-fishfooding
export SERVICE_NAME=genai-app-sample
export REGION=us-central1
```

-   `PROJECT_ID`: Your Google Cloud project ID.
-   `SERVICE_NAME`: The name of your Cloud Run service.
-   `REGION`: The region where you want to deploy your service.

### 2. Deploy the Streamlit App

To deploy your Streamlit app, follow these steps:

1. Build and deploy the Streamlit app to Cloud Run:

    ```bash
    # Create a temporary directory for deployment
    rm -rf temp-streamlit-deployment && mkdir temp-streamlit-deployment

    # Copy the necessary files to the temporary directory
    cp ./pyproject.toml ./README.md ./poetry.lock temp-streamlit-deployment/
    cp -r ./app temp-streamlit-deployment/
    cp -r ./streamlit temp-streamlit-deployment/
    cp ./streamlit/streamlit_app.dockerfile temp-streamlit-deployment/Dockerfile

    # Deploy the app to Cloud Run
    gcloud run deploy $SERVICE_NAME \
      --source temp-streamlit-deployment \
      --project $PROJECT_ID \
      --service-account $SERVICE_NAME-cr-sa@$PROJECT_ID.iam.gserviceaccount.com \
      --region $REGION \
      --port 8501
      
    # Clean up the temporary directory:
    rm -rf temp-streamlit-deployment
    ```

### 3. Set Up Identity-Aware Proxy (IAP)

#### a. Create IAP Service Identity

```bash
gcloud beta services identity create --service=iap.googleapis.com --project $PROJECT_ID
```

#### b. Get Project Number

```bash
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
```

#### c. Grant IAP Service Account Permission

```bash
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com" \
  --role='roles/run.invoker' \
  --project $PROJECT_ID \
  --region=$REGION
```

#### d. Enable IAP for Backend Service

Choose one of the following options based on your setup:

##### For Global Backend Service

```bash
gcloud compute backend-services update $SERVICE_NAME \
  --global \
  --iap=enabled \
  --project $PROJECT_ID
```

##### For Regional Backend Service

```bash
gcloud compute backend-services update $SERVICE_NAME \
  --region=$REGION \
  --iap=enabled \
  --project $PROJECT_ID
```

#### e. Create Load Balancer with Serverless NEG

> **Note:** This step is currently missing and needs to be implemented.
