import boto3
import luigi
import paramiko
import time
import json
import os
import yaml
import sys
import socket
from luigi.mock import MockFile
from securitygroup_check import SecurityGroupCheck
from print_to_mongodb import TaskPrinterToMongo

taskPrinter = TaskPrinterToMongo()
taskId = 0
#the log is written by python.

class StartInstanceTask(luigi.Task):
    task_namespace = 'aws'

    def requires(self):
        return SecurityGroupCheck()

    def output(self):
        return MockFile('InstanceInfo')

    def run(self):
        #read from ParseParameters
        sys.stdout.flush()
        with self.input().open('r') as infile:
            params = json.load(infile)
        taskId = int(params['taskId'])
        
        taskPrinter.createTask(taskId, task_type = 'TensorFlow', task_info = 'Starting TensorFlow Service 									')
        #set TaskDB fields
        try:
            taskPrinter.debugInfo(taskId, str(params))
            taskPrinter.setDuration(taskId, params['duration'])
            taskPrinter.setCredentialOwner(taskId, params['credentialOwner'])
            taskPrinter.setModule(taskId, params['module']+'-'+params['username'])
        except:
            taskPrinter.updateError(taskId, 'Read params failed')
            taskPrinter.failTask(taskId)
            sys.exit()


        time.sleep(3)
        taskPrinter.updateTaskRespose(taskId, 'Step1: Reading configuration from config file.')
        taskPrinter.updateTaskRespose(taskId, 'Step1: Complete.')

        time.sleep(3)
        taskPrinter.updateTaskRespose(taskId, "Step2: Creating new EC2 instance.")
        
        ec2 = boto3.resource('ec2',
                            aws_access_key_id=params['accessKeyID'],
                            aws_secret_access_key=params['secretAccessKey'],
                            region_name = params['regionName'])
        
        #TODO: ami id check
        imgid = params['amiId']

        # Configuration scripts for the instances when launching
        instance_config = """#!/bin/bash
		sudo docker run -p 9000:9000 ganecrxunpeng.azurecr.io/tensorflow-serving tensorflow_model_server --port=9000 --model_name=inception --model_base_path=/root/serving/inception-export/
		"""

        instance = ec2.create_instances(
            ImageId=imgid,
            MinCount=1,
            MaxCount=1,
            KeyName=params['pemName'],
            SecurityGroupIds=[
                params['securityGroup'],
            ],
            UserData=instance_config,
            InstanceType=params['flavor'],
        )
        
        taskPrinter.updateTaskRespose(taskId, "Step2: EC2 Instance Created!")
        time.sleep(5)

        #assume AWS return IP in 20 seconds
        # time.sleep(20)
        new_id = instance[0].id
        new_ip = ''
        ec2 = boto3.resource('ec2',
                            aws_access_key_id=params['accessKeyID'],
                            aws_secret_access_key=params['secretAccessKey'],
                            region_name = params['regionName'])
        for ins in ec2.instances.all():
            if ins.id == new_id:
                #print(ins.public_ip_address)
                new_ip = ins.public_ip_address
        
        params['targetIP'] = new_ip
        _out = self.output().open('w')
        json.dump(params,_out)
        _out.close()

        time.sleep(50)
        taskPrinter.updateTaskRespose(taskId, "Step2: Complete.")
        time.sleep(5)


class StartMatlab(luigi.Task):
    task_namespace = 'aws'

    def requires(self):
        return StartInstanceTask()

    def run(self):
        #read params
        with self.input().open('r') as infile:
            #print(infile)
            params = json.load(infile)

        # DOCKER_NOTEBOOK_IMAGE = params['imageName']
        USER_NAME = params['username']
        ip = params['targetIP']
        taskId = params['taskId']
        
        time.sleep(5)
        taskPrinter.updateTaskRespose(taskId, 'Step3: Starting TensorFlow service for inception at - '+ip+'.')
        # print('Step4: Starting Matlab at - '+ip+'.')
        # sys.stdout.flush()

        time.sleep(5)
        # Matlab Instruction
        taskPrinter.updateTaskRespose(taskId, 'step4: Please open your terminal and go to default foulder: cd ~')
        taskPrinter.updateTaskRespose(taskId, 'Step5: Clone TensorFlow serving : git clone --recurse-submodules https://github.com/tensorflow/serving.git')
        taskPrinter.updateTaskRespose(taskId, 'step6: install TensorFlow Serving Python API PIP package: pip install tensorflow-serving-api')
        taskPrinter.updateTaskRespose(taskId, 'step7: Test service: python /default-path/serving/tensorflow_serving/example/inception_client.py --server={AWS instance ip}:9000 --image=/default-path/image_inception.jpg')


        time.sleep(5)

        print('ip: '+ip)
        sys.stdout.flush()
        #taskPrinter.updateTaskRespose(taskId, 'test:' + ip)
        taskPrinter.completeTask(taskId, 'http://' + ip)

if __name__ == '__main__':
    luigi.run(['aws.StartMatlab', '--local-scheduler', '--no-lock'])
