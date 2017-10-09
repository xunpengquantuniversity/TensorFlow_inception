# TensorFlow_inception
AMI base image(ubuntu 16.04): 
* ami-6c8b7514: mcr: base T-SNE

# Server 
## AMI creation in AWS
###  1. create new AMI instance
    
    #security-groups: jupyterhub, matlab(we use this one here)
    aws ec2 run-instances --image-id ami-6c8b7514 --count 1 --instance-type t2.micro --key-name jaja --security-groups {security-groups} | grep InstanceId
    # return "InstanceId": "i-0e1c106480562bc33"

    # How to create a new instance with specific volume size using --block-device-mapping
    aws ec2 run-instances --image-id ami-6c8b7514 --count 1 --instance-type t2.large --key-name jaja --security-groups matlab --block-device-mapping "[ { \"DeviceName\": \"/dev/sda1\", \"Ebs\": { \"VolumeSize\": 50 } } ]" | grep InstanceId
    

### 2. get ip address of the instance
    
    aws ec2 describe-instances --instance-ids {instance-id} | grep PublicIpAddress
    

### 3. Login the instance 
    
    ssh -i jaja.pem ubuntu@{ip}
    

### 4. install docker in AWI instance

### 5. install azure in AWI instance(get docker image from az container registry)
    
    echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ wheezy main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
    sudo apt-key adv --keyserver packages.microsoft.com --recv-keys 417A0893
    sudo apt-get install apt-transport-https
    sudo apt-get update && sudo apt-get install azure-cli
    

### 6. Login az and pull docker image from Azure to local
    
    # show username and password for your own az container registry
    az acr credential show --name=ganEcrxunpeng
    # login with username and password
    docker login ganecr.azurecr.io -u=ganEcr -p=<password value from credentials>
    

### 7. Run Docker images bind port 9000 in container to localhost:9000 and create a new container
    sudo docker run -p 9000:9000 ganecrxunpeng.azurecr.io/tensorflow-serving tensorflow_model_server  --port=9000 --model_name=inception --model_base_path=/root/serving/inception-export
    

### 9. Consume service from remote host:
    
    python inception_client.py --server={instance ip}:9000 --image={path}/image3.jpg
    

### 10. start docker instance in AWS instance:
    
    sudo docker start -i docker {instance name}
    

### 11. Create AMI image 
    
    aws ec2 create-image --instance-id {instance you want to create} --name "TensorFlow Inception AMI" --description "This is a AMI for TensorFlow AMI"
    # return a New AMI image: "ImageId": "ami-09c50071"
    
# Client
### 1. Get the TensorFlow Serving
    # It is pretty simple — just clone the repository:
    cd ~
    git clone --recurse-submodules https://github.com/tensorflow/serving.git
    
### 2. Download image from website to default folder
    https://www.google.com/search?q=cat+256*256&tbm=isch&tbo=u&source=univ&sa=X&ved=0ahUKEwir-cPQ6tnWAhWCQCYKHXDnDXMQsAQIJw&biw=1440&bih=782#imgrc=4LAEY17JmVkiQM:
    Place this image to current folder and rename it to image_inception.jpg
### 3. install TensorFlow Serving Python API PIP package
    pip install tensorflow-serving-api
### 4. test service
    python /default-path/serving/tensorflow_serving/example/inception_client.py --server={AWS instance ip}:9000 --image=/default-path/image_inception.jpg


# Set up Server
### 1. create new AWI instance
    aws ec2 run-instances --image-id ami-09c50071 --count 1 --instance-type t2.micro --key-name jaja --security-groups {security-groups} | grep InstanceId

### 2. get ip address of the instance
    
    aws ec2 describe-instances --instance-ids {instance-id} | grep PublicIpAddress
    
### 3. Login the instance 
    
    ssh -i jaja.pem ubuntu@{ip}
    
### 4. start docker instance in AMI and get in docker instance shell
    sudo docker start -i bbd41f1fa1c8

### 5. start service in docker instance
    tensorflow_model_server --port=9000 --model_name=inception --model_base_path=/root/serving/inception-export/

# server and secondary service
    python /home/ubuntu/serving/tensorflow_serving/example/inception_client.py --server=localhost:9000 --image=/home/ubuntu/image3.jpg
### cp picture from docker container to local AMI 
    sudo docker cp 99df3a5bc0ac:/root/serving/image3.jpg .

# Flask API
http://www.datasciencebytes.com/bytes/2015/02/24/running-a-flask-app-on-aws-ec2/
