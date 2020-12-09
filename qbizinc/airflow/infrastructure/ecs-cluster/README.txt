Must use terraform.  You may want to change the variables defined in the terraform.tfvars file
to avoid naming collisions with others working in the same account.

1) Install Terriform from HashiCorp.
2) run `terraform init`
3) run `terraform apply -var-file terraform.tfvars`


Remove resources with `terraform destroy`
