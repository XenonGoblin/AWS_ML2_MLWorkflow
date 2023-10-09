# Draft Lambdas and Step Function Workflow

# Your operations team uses Step Functions to orchestrate serverless workflows. 
# One of the nice things about Step Functions is that [workflows can call other workflows](https://docs.aws.amazon.com/step-functions/latest/dg/connect-stepfunctions.html), so the team can easily plug your workflow into the broader production architecture for Scones Unlimited.

# In this next stage you're going to write and deploy three Lambda functions, and then use the Step Functions visual editor to chain them together! 
# Our functions are going to work with a simple data object:

{
    "inferences": [], # Output of predictor.predict
    "s3_key": "", # Source data S3 key
    "s3_bucket": "", # Source data S3 bucket
    "image_data": ""  # base64 encoded string containing the image data
}


# A good test object that you can use for Lambda tests and Step Function executions, throughout the next section, might look like this:

{
  "image_data": "",
  "s3_bucket": "sagemaker-us-east-1-605922365623",
  "s3_key": "test/bicycle_s_000513.png"
}

# Using these fields, your functions can read and write the necessary data to execute your workflow. 
# Let's start with the first function. Your first Lambda function will copy an object from S3, base64 encode it, and then return it to the step function as `image_data` in an event.

# Go to the Lambda dashboard and create a new Lambda function with a descriptive name like "serializeImageData" and select thr 'Python 3.8' runtime. 
# Add the same permissions as the SageMaker role you created earlier. (Reminder: you do this in the Configuration tab under "Permissions"). 
# Once you're ready, use the starter code below to craft your Lambda handler:

import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key = event["s3_key"]
    bucket = event["s3_bucket"]
    
    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, "/tmp/image.png")
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }


# The next function is responsible for the classification part - we're going to take the image output from the previous function, decode it, 
#     and then pass inferences back to the the Step Function.

# Because this Lambda will have runtime dependencies (i.e. the SageMaker SDK) you'll need to package them in your function. 
# *Key reading:* https://docs.aws.amazon.com/lambda/latest/dg/python-package-create.html#python-package-create-with-dependency

# Create a new Lambda function with the same rights and a descriptive name, then fill in the starter code below for your classifier Lambda.


import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key = event["s3_key"]
    bucket = event["s3_bucket"]
    
    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, "/tmp/image.png")
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }


# Finally, we need to filter low-confidence inferences. Define a threshold between 1.00 and 0.000 for your model: what is reasonble for you? 
# If the model predicts at `.70` for it's highest confidence label, do we want to pass that inference along to downstream systems? 
# Make one last Lambda function and tee up the same permissions:


import json

THRESHOLD = .70

def lambda_handler(event, context):
    
    # Grab the inferences from the event
    inferences = event["inferences"]
    
    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = any([float(x.split(":")[1]) >= THRESHOLD for x in inferences.split(",")])
    
    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }

# Once you have tested the lambda functions, save the code for each lambda function in a python script called 'lambda.py'.

# With your lambdas in place, you can use the Step Functions visual editor to construct a workflow that chains them together. 
# In the Step Functions console you'll have the option to author a Standard step function *Visually*.

# When the visual editor opens, you'll have many options to add transitions in your workflow.
# We're going to keep it simple and have just one: to invoke Lambda functions. 
# Add three of them chained together. For each one, you'll be able to select the Lambda functions you just created in the proper order, filter inputs and outputs, 
# and give them descriptive names.

# Make sure that you:

# 1. Are properly filtering the inputs and outputs of your invokations (e.g. `$.body`)
# 2. Take care to remove the error handling from the last function - it's supposed to "fail loudly" for your operations colleagues!

# Take a screenshot of your working step function in action and export the step function as JSON for your submission package.