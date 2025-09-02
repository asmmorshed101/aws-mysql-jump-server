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
    
    Copy code from main.py file 

   ```
 5. Preview the planned changes:
    ```bash
    pulumi preview
    ```
    ![Alt text](images/1.%20pulumi%20preview.png)
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
 
