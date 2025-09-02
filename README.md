 # AWS MySQL Jump Host using pulumi

 This project demonstrates the creation of a secure AWS VPC environment with public and private subnets, a bastion (jump) host, and a private MySQL database. The bastion host allows secure SSH access to instances in the private subnet, enabling management of the MySQL server without exposing it to the Internet.

 ## Overview

  - Creating a VPC, two Subnet, Public and private instance, Security group, NAT, IGW.
  - Accessing private subnet from local using jump host
  - mysql installation using pulumi code and access from Bastion host

 ## Prerequisites

 - AWS credentials configured in your environment (for example via AWS CLI or environment variables).
 - Python installed.
 - Pulumi CLI already installed and logged in.

 ## Getting Started

 1. Generate a new project from this template:
    ```bash
    pulumi new aws-python
    ```
 2. Follow the prompts to set your project name and AWS region (default: `us-east-1`).
 3. Change into your project directory:
    ```bash
    cd <project-name>
    ```
 4. This is the full code for creating above configuration in aws
   ```bash
   import pulumi
   import pulumi_aws as aws

   # Create a VPC
   vpc = aws.ec2.Vpc("my-vpc",
      cidr_block="10.0.0.0/16",
      tags= {
      "Name":  "my-vpc"
      }
   )

   pulumi.export("vpc_id", vpc.id)

   # Create a public subnet
   public_subnet = aws.ec2.Subnet("public-subnet",
      vpc_id=vpc.id,
      cidr_block="10.0.1.0/24",
      availability_zone="ap-southeast-1a",
      map_public_ip_on_launch=True,
      tags= {
      "Name":  "public-subnet"
      }
   )

   pulumi.export("public_subnet_id", public_subnet.id)

   # Create a private subnet
   private_subnet = aws.ec2.Subnet("private-subnet",
      vpc_id=vpc.id,
      cidr_block="10.0.2.0/24",
      availability_zone="ap-southeast-1a",
      tags= {
      "Name":  "private-subnet"
      }
   )

   pulumi.export("private_subnet_id", private_subnet.id)

   # Create an Internet Gateway
   igw = aws.ec2.InternetGateway("internet-gateway",
      vpc_id=vpc.id,
      tags= {
      "Name":  "igw"
      }
   )

   pulumi.export("igw_id", igw.id)

   # Create a route table
   public_route_table = aws.ec2.RouteTable("public-route-table",
      vpc_id=vpc.id,
      tags= {
      "Name":  "rt-public"
      }
   )

   # Create a route in the route table for the Internet Gateway
   route = aws.ec2.Route("igw-route",
      route_table_id=public_route_table.id,
      destination_cidr_block="0.0.0.0/0",
      gateway_id=igw.id
   )

   # Associate the route table with the public subnet
   route_table_association = aws.ec2.RouteTableAssociation("public-route-table-association",
      subnet_id=public_subnet.id,
      route_table_id=public_route_table.id
   )

   pulumi.export("public_route_table_id", public_route_table.id)


   # Allocate an Elastic IP for the NAT Gateway
   eip = aws.ec2.Eip("nat-eip")

   # Create the NAT Gateway
   nat_gateway = aws.ec2.NatGateway("nat-gateway",
      subnet_id=public_subnet.id,
      allocation_id=eip.id,
      tags= {
      "Name":  "nat"
      }
   )

   pulumi.export("nat_gateway_id", nat_gateway.id)


   # Create a route table for the private subnet
   private_route_table = aws.ec2.RouteTable("private-route-table",
      vpc_id=vpc.id,
      tags= {
      "Name":  "rt-private"
      }
   )

   # Create a route in the route table for the NAT Gateway
   private_route = aws.ec2.Route("nat-route",
      route_table_id=private_route_table.id,
      destination_cidr_block="0.0.0.0/0",
      nat_gateway_id=nat_gateway.id
   )

   # Associate the route table with the private subnet
   private_route_table_association = aws.ec2.RouteTableAssociation("private-route-table-association",
      subnet_id=private_subnet.id,
      route_table_id=private_route_table.id
   )

   pulumi.export("private_route_table_id", private_route_table.id)


   # Create a security group for the public instance
   public_security_group = aws.ec2.SecurityGroup("public-secgrp",
      vpc_id=vpc.id,
      description='Enable HTTP and SSH access for public instance',
      ingress=[
         {'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0']},
         {'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']}
      ],
      egress=[
         {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']}
      ]
   )

   # Use the specified Ubuntu 24.04 LTS AMI
   ami_id = 'ami-060e277c0d4cce553'


   # User Data script for User Creation and roo user access off

   user_data_script = """#!/bin/bash

   # Update packages and install mysql-client
   apt-get update -y
   apt-get install -y mysql-client

   # Create ops user with sudo privileges
   adduser --disabled-password --gecos "" ops
   mkdir -p /home/ops/.ssh
   chown ops:ops /home/ops/.ssh
   chmod 700 /home/ops/.ssh

   # Copy authorized_keys from default ubuntu user (from MyKeyPair)
   cp /home/ubuntu/.ssh/authorized_keys /home/ops/.ssh/
   chown -R ops:ops /home/ops/.ssh
   chmod 600 /home/ops/.ssh/authorized_keys

   # Paste your PEM file manually here into id_ecdsa
   cat << 'EOF' > /home/ops/.ssh/id_ecdsa
   -----BEGIN RSA PRIVATE KEY-----

   Pem code key here

   -----END RSA PRIVATE KEY-----
   EOF

   # Set proper permissions for the private key
   chown ops:ops /home/ops/.ssh/id_ecdsa
   chmod 400 /home/ops/.ssh/id_ecdsa

   # Give ops user sudo privileges
   usermod -aG sudo ops

   # Harden SSH
   sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
   sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
   systemctl restart sshd
   """


   # Create an EC2 instance in the public subnet
   public_instance = aws.ec2.Instance("public-instance",
      instance_type="t2.micro",
      vpc_security_group_ids=[public_security_group.id],
      ami=ami_id,
      subnet_id=public_subnet.id,
      key_name="MyKeyPair",
      associate_public_ip_address=True,
      user_data=user_data_script,
      tags= {
      "Name":  "public-ec2"
      }
   )

   pulumi.export("public_instance_id", public_instance.id)
   pulumi.export("public_instance_ip", public_instance.public_ip)


   # Create a security group for the private instance
   private_security_group = aws.ec2.SecurityGroup("private-secgrp",
      vpc_id=vpc.id,
      description='Enable SSH access for private instance',
      ingress=[
         {'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'security_groups': [public_security_group.id]},
         # MySQL from public security group
         {'protocol': 'tcp', 'from_port': 3306, 'to_port': 3306, 'security_groups': [public_security_group.id]}
      
      ],
      egress=[
         {'protocol': '-1', 'from_port': 0, 'to_port': 0, 'cidr_blocks': ['0.0.0.0/0']}
      ]
   )


   import random
   import string

   # Generate a random password for appuser
   appuser_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

   private_user_data = f"""#!/bin/bash
   # Update packages
   for i in {{1..10}}; do
   apt-get update && break || sleep 30
   done

   apt-get install -y mysql-server mysql-client

   # Enable and start MySQL service
   systemctl enable mysql
   systemctl start mysql

   # Configure MySQL to listen on private IP and localhost
   PRIVATE_IP=$(hostname -I | awk '{{print $1}}')
   sed -i "s/bind-address.*/bind-address = 127.0.0.1/" /etc/mysql/mysql.conf.d/mysqld.cnf
   echo "bind-address = ${{PRIVATE_IP}}" >> /etc/mysql/mysql.conf.d/mysqld.cnf
   systemctl restart mysql

   # Secure installation (disable remote root, remove test db)
   mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '';"
   mysql -e "DELETE FROM mysql.user WHERE User='';"
   mysql -e "DROP DATABASE IF EXISTS test;"
   mysql -e "FLUSH PRIVILEGES;"

   # Create appdb and appuser
   mysql -e "CREATE DATABASE appdb;"
   mysql -e "CREATE USER 'appuser'@'%' IDENTIFIED BY '{appuser_password}';"
   mysql -e "GRANT ALL PRIVILEGES ON appdb.* TO 'appuser'@'%';"
   mysql -e "FLUSH PRIVILEGES;"
   """

   # Pulumi export for password so you can access it later
   pulumi.export("appuser_password", appuser_password)

   # Create an EC2 instance in the private subnet
   private_instance = aws.ec2.Instance("private-instance",
      instance_type="t2.micro",
      vpc_security_group_ids=[private_security_group.id],
      ami=ami_id,
      subnet_id=private_subnet.id,
      key_name="MyKeyPair",
      user_data=private_user_data,
      tags= {
      "Name":  "private-ec2"
      },
      opts=pulumi.ResourceOptions(
               depends_on=[nat_gateway]  
         )
   )

   pulumi.export("private_instance_id", private_instance.id)
   pulumi.export("private_instance_ip", private_instance.private_ip)


   ```
 5. Preview the planned changes:
    ```bash
    pulumi preview
    ```
    ![Alt text](images/1.%20pulumi%20preview.png.png)
 6. Deploy the stack:
    ```bash
    pulumi up
    ```
    ![Alt text](images/2.%20pulumi%20up.png)
    ![Alt text](images/3.%20pulumi%20up%20yes.png)
 
 ## Here is the output when you write jump server command
   ```bash
   ssh -J user@bastionip user@privateip
   ```
   ![Alt text](images/4.%20jump.png)
   ![Alt text](images/5.%20jump.png)

 ## check mysql in private instance where it is installed
  ```bash
   mysql -u appuser -p -e "SHOW DATABASES;"
  ```
  ![Alt text](images/6.%20mysql%20db%20.png)
 ## check mysql db status
  ```bash
  systemctl status mysql
  ```
  ![Alt text](images/7.%20mysql%20status.png)
  
  ## Now from bastion host access mysql
  ```bash
  mysql -h private-intance-ip -u appuser -p -e "SELECT 1;"
  ``` 
  ![Alt text](images/8.%20bastion%20host%20to%20mysql.png)
 7. Destroy the configuration:
    ```bash
    pulumi destroy
    ```
 ![Alt text](images/9.%20pulumi%20destroy.png)
 8. And also type
   ```bash
    pulumi stack rm dev
    ```
  ![Alt text](images/10.%20pulumi%20destroy.png)


### Project Complete
This concludes the setup and demonstration of the AWS VPC with bastion host and private MySQL access.
 
