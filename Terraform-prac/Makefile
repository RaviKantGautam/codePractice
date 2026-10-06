.PHONY: init fmt validate plan apply destroy

init:
	terraform init

fmt:
	terraform fmt -recursive

validate: fmt
	terraform validate

plan: validate
	terraform plan

apply: validate
	terraform apply

destroy:
	terraform destroy
