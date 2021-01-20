provider "google" {
  credentials = file("your-service-user-credential.json")
  project     = "your-project-id"
}

module "miniflux" {
  source  = "huy-nguyen/miniflux/google"
  version = "4.0.0"

  region = "us-east1"
  zone   = "us-east1-d"
  private_services_access_ip_range = {
    starting_address = "192.168.16.0"
    prefix_length    = 20
  }

  serverless_vpc_access_connector_ip_range = "10.8.0.16/28"
  sql_instance_machine_type                = "db-f1-micro"
  db_user_password                         = "pick_a_strong_password"
}

# These values are used to create `app.yaml` configuration for App Engine:
output "vpc_access_connector_id" {
  value = module.miniflux.vpc_access_connector_id
}

output "sql_connection_name" {
  value = module.miniflux.sql_connection_name
}

output "sql_instance_user" {
  value = module.miniflux.sql_instance_user
}

output "database_url" {
  value = module.miniflux.database_url
}
