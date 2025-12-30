#!/bin/bash
# Complete AWS EC2 deployment from CLI
# Run: ./deploy_to_aws.sh

set -e

echo "🚀 NBA Decision Engine - AWS CLI Deployment"
echo ""

# Configuration
KEY_NAME="nba-app-key"
SECURITY_GROUP_NAME="nba-app-sg"
INSTANCE_NAME="nba-decision-engine"
INSTANCE_TYPE="t2.micro"  # Change to t3.small for better performance
REGION="us-east-1"  # Change if needed

# Get your public IP for SSH access
MY_IP=$(curl -s https://checkip.amazonaws.com)
echo "📍 Your IP: $MY_IP"
echo ""

# Step 1: Create key pair if doesn't exist
echo "🔑 Creating SSH key pair..."
if [ -f "$KEY_NAME.pem" ]; then
    echo "   Key pair already exists locally"
else
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text \
        --region $REGION > $KEY_NAME.pem
    chmod 400 $KEY_NAME.pem
    echo "   ✅ Created and saved $KEY_NAME.pem"
fi
echo ""

# Step 2: Create security group
echo "🔒 Creating security group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Security group for NBA Decision Engine" \
    --region $REGION \
    --output text \
    --query 'GroupId' 2>/dev/null || \
    aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

echo "   Security Group ID: $SG_ID"

# Add rules
echo "   Adding firewall rules..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr $MY_IP/32 \
    --region $REGION 2>/dev/null || echo "   SSH rule already exists"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "   HTTP rule already exists"

echo "   ✅ Security group configured"
echo ""

# Step 3: Launch EC2 instance
echo "🖥️  Launching EC2 instance ($INSTANCE_TYPE)..."

# Get latest Amazon Linux 2023 AMI
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" \
    "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text \
    --region $REGION)

echo "   Using AMI: $AMI_ID"

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --region $REGION \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "   Instance ID: $INSTANCE_ID"
echo "   ⏳ Waiting for instance to start..."

aws ec2 wait instance-running \
    --instance-ids $INSTANCE_ID \
    --region $REGION

echo "   ✅ Instance is running!"
echo ""

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "🌐 Instance Public IP: $PUBLIC_IP"
echo ""

# Wait a bit more for SSH to be ready
echo "⏳ Waiting 30s for SSH to be ready..."
sleep 30

# Step 4: Deploy application
echo "📦 Deploying application..."
echo ""

ssh -i $KEY_NAME.pem -o StrictHostKeyChecking=no ec2-user@$PUBLIC_IP << 'ENDSSH'
# Update system
echo "📦 Updating system..."
sudo yum update -y

# Install Docker
echo "🐳 Installing Docker..."
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Git
echo "📚 Installing Git..."
sudo yum install -y git

# Clone repo
echo "📥 Cloning repository..."
git clone https://github.com/BharathPalanisamy/NBA-decision-Engine.git nba-decision-engine
cd nba-decision-engine

# Build Docker image
echo "🏗️  Building Docker image..."
sudo docker build -t nba-decision-engine .

# Run container
echo "▶️  Starting application..."
sudo docker run -d \
    --name nba-app \
    -p 80:8501 \
    --restart unless-stopped \
    nba-decision-engine

echo ""
echo "✅ Deployment complete!"
ENDSSH

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🌐 Application URL: http://$PUBLIC_IP"
echo "🔑 SSH Access: ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo "📊 View logs: ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP 'sudo docker logs -f nba-app'"
echo ""
echo "💰 Estimated cost: ~$8/month (t2.micro) or FREE for 12 months"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Save these details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  Key file: $KEY_NAME.pem (keep this safe!)"
echo ""
