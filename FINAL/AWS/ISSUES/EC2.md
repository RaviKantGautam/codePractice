# EC2 instance connection timeout error

Domain pointing -> VPC -> internet gateway -> routing table -> Network ACLs -> security group

# [EC2 Auto Scaling Group Issues](https://youtu.be/0cJRXZ7PrDk?si=M0hxCe9ue31raUvM)

1. Check your scaling policies to see whether an event triggers more than one policy.
2. Verify if a scale-out policy and a scale-in policy are triggered at the same time.
3. Check if your Auto Scaling group already reached its minimum or maximum number of instances. ( check for what values are set in desired, minimum and maximum capacity. Good practice to give double the capacity for maximum over the desired capacity )
4. Check if your instances are in a cooldown period or instance warmup period. ( Default cooldown 300 sec and Default warmup 60 sec)
5. Check if there is a lifecycle hook configured for your EC2 Auto Scaling group. ( like updating pckages on the start of a new instance)
6. Check is there is any scheduled action configured the auto scaling group.
7. Check suspended processes for your auto scaling group.
