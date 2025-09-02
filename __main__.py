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
MIIEowIBAAKCAQEAuVERgcvn2EMEaqxluv3mK2qwxApYVLVAI81eYmn1btrJIFA/
Gm2dbvroNZDmwE7nbJ4FWffHAsR/3/PthtMOmRFc49bHBBUU7tt3L6RqvZ3slmKT
WNA2MXFXgC3H5TDJqaiiJabKcGHHFkoKfcwH5SWO5QNkxOIsde0cxvE5xH/ixeV6
mRtNZsG2HCnggdr1pg6MgN1jCbIcmQOfD67BHHHNRrqiA3qruPuD3dizNoTngeA2
PHiUUcEwJsMw/fPyRsVapGbFMkttZWsZa7CuYKU8yt4x4VbIB6zRpdN0DEgR2z65
c2RHPwFEtWPjwzbfDtiRaEI6sQKVYpJtM80+ZQIDAQABAoIBAG6Py14hBUWlVjE+
gcM6T+R/Vs7fTSvcp1O05ybYCLIGnhBFUCC4XUElOP0cYk9BxBitfovapEUmbxRy
N7hEm2T/Uugr77ijy0VmcoleEsDmQ4zFaxuFvY9qC8ZRif1XSjmKfpLwG79I1rqZ
mgDLhbpU2hgQGkLMnbINsSmQKeLtVGWpq84/YoAMajrPoxNbcJABFBhlQqqviHWD
r/tw79qUdOKw3HZvohTdRd8PDcLZwF9t2cMw3lnRPZS+nf2GXKrCJ5M385eMfIhN
vhr2q0BsDCywL+lUKJ4L8rjSERdHmHcn2GNbbh6pSKBN8KuOa9F50oDk9ETDDfXq
Nj3F9gECgYEA8RO9PwsNdkWtJXtrylzjodfj2PnL3sSxAulELDUYnKzzD4/LSN41
H4EWW8wPhfQgqIFsOE/lgHttV45vGy5uAJq/X9T+Pawa3MI59THvNVydxejZpsj1
HxsE88okfS+DIElWrB8B7Tao0LvYTHxg2ntjG9zsk4HOMh81uBycrKECgYEAxMm2
xWpqcM++XHbGbbOg9KnU4OC0k79st7Sk73Edx/bkOlrXkux3b1QNhb8MRK+uu8J5
iUU1OzVRklD2IF0tuWj8kABb8K1k/s99QgY8hYOTT6WEqEKZHbAaOudOaw4oYstW
Y/FWbQhFVuul7lHrhfpRyh4ntaEvSglaD63oV0UCgYAH0Cf1/xm0l5WA/XsE1/XY
rPKJea8NzTofagf3ltDxYvmNq49fETSPjNN4rihiowLb8zXarVw2yclFaSxYqSyP
gHRrWq/St903AmR2eePSyumiHGXRbfnjxDBo5khAdmW9iiLw+SBK29akzTG5aN6K
ti0EHijcrvxLy48mJGc/gQKBgQCmV/Q9cDTFY3YAZw5YkOzPo/ekl41NDxTxPKvn
EvEfpN1LTprHQUe8PYqosdPHA9JqOHvPw0a549ouGm3S8bDC97H2b7dH/OpQUkgJ
VYg3O/975ef660DOzZt+iyPIbtFIoaVHGiv6QnGKhetfRrQWLoCQn2jlqXh11u3g
LxslGQKBgA2rAVKIrNsDUAEGIkMY3R3BSg6M/8V3eju4kdgs6O1WI1fBObHpX9jz
uXHPlK1EKRoOFOQ7pyKVaokub/qTEStI1LFs8REDorQRH+YRtfWIyFROgca+qYFv
Mw016H60KZ8SjNJNMrw4E9EbvmZqG4C9WSLLp/1kZNhWdCRnC/h5
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
        {'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'security_groups': [public_security_group.id]}
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


