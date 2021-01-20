def generate_config(context):
    properties = context.properties
    project_id = context.env["project"]

    # Required properties:
    region = properties["region"]
    private_services_access_ip_range_prefix_length = properties[
        "privateServicesAccessIpRange"
    ]["prefixLength"]
    private_services_access_ip_range_starting_address = properties[
        "privateServicesAccessIpRange"
    ]["startingAddress"]
    serverless_vpc_access_connector_ip_range = properties[
        "serverlessVpcAccessConnectorIpRange"
    ]
    zone = properties["zone"]
    cloud_sql_instance_name = properties["cloudSqlInstanceName"]
    sql_machine_instance_type = properties["sqlMachineInstanceType"]
    db_user_password = properties["dbUserPassword"]

    sql_instance_disk_type = properties.get("sqlInstanceDiskType", "PD_SSD")

    network_resource_name = "network"
    network_name = "miniflux-network"

    network_resource = {
        "name": network_resource_name,
        "type": "network.py",
        "properties": {"name": network_name, "autoCreateSubnetworks": False},
    }

    private_services_access_ip_reserved_ip_range_resource_name = (
        "private-services-access-reserved-ip-range"
    )
    private_services_access_reserved_ip_range_name = (
        "google-managed-services-" + network_name
    )

    private_services_reserved_ip_range_resource = {
        "name": private_services_access_ip_reserved_ip_range_resource_name,
        "type": "gcp-types/compute-v1:globalAddresses",
        "properties": {
            "name": private_services_access_reserved_ip_range_name,
            "purpose": "VPC_PEERING",
            "addressType": "INTERNAL",
            "network": "$(ref." + network_resource_name + ".selfLink)",
            "prefixLength": private_services_access_ip_range_prefix_length,
            "address": private_services_access_ip_range_starting_address,
        },
    }

    private_services_access_peering_connection_resource_creation_name = (
        "private-services-access-peering-connection-create"
    )

    service_networking_api_url = "servicenetworking.googleapis.com"

    private_services_access_peering_connection_resource = {
        "name": private_services_access_peering_connection_resource_creation_name,
        "action": project_id
        + "/service-networking-v1:servicenetworking.services.connections.create",
        "metadata": {
            "dependsOn": [
                network_resource_name,
                private_services_access_ip_reserved_ip_range_resource_name,
            ],
            "runtimePolicy": ["CREATE"],
        },
        "properties": {
            "parent": "services/" + service_networking_api_url,
            "reservedPeeringRanges": [private_services_access_reserved_ip_range_name],
            "network": "projects/" + project_id + "/global/networks/" + network_name,
        },
    }

    vpc_access_connector_create_action_name = "vpc-access-connector-create"
    connector_id = properties.get(
        "serverlessVpcAccessConnectorName", "miniflux-connector"
    )
    connector_name = (
        "projects/"
        + project_id
        + "/locations/"
        + region
        + "/connectors/"
        + connector_id
    )

    vpc_access_connector_create_action = {
        "name": vpc_access_connector_create_action_name,
        "action": project_id
        + "/vpc-access-v1:vpcaccess.projects.locations.connectors.create",
        "metadata": {"runtimePolicy": ["CREATE"]},
        "properties": {
            "network": network_name,
            "ipCidrRange": serverless_vpc_access_connector_ip_range,
            "minThroughput": 200,
            "maxThroughput": 300,
            "connectorId": connector_id,
            "parent": "projects/" + project_id + "/locations/" + region,
        },
    }

    vpc_access_connector_delete_action_name = "vpc-access-connector-delete"
    vpc_access_connector_delete_action = {
        "name": vpc_access_connector_delete_action_name,
        "action": project_id
        + "/vpc-access-v1:vpcaccess.projects.locations.connectors.delete",
        "metadata": {"runtimePolicy": ["DELETE"]},
        "properties": {
            "name": connector_name,
        },
    }

    db_name = properties.get("dbName", "miniflux-db")
    db_user_name = properties.get("dbUserName", "miniflux")
    cloud_sql_instance_resource_name = "sql-instance"

    cloud_sql_instance_resource = {
        "name": cloud_sql_instance_resource_name,
        "type": "cloud-sql.py",
        "properties": {
            "name": cloud_sql_instance_name,
            "region": region,
            "databaseVersion": "POSTGRES_12",
            "settings": {
                "tier": sql_machine_instance_type,
                "dataDiskType": sql_instance_disk_type,
                "locationPreference": {"zone": zone},
                "ipConfiguration": {
                    "ipv4Enabled": False,
                    "privateNetwork": "$(ref." + network_resource_name + ".selfLink)",
                },
            },
            "users": [{"name": db_user_name, "password": db_user_password}],
            "databases": [{"name": db_name}],
            "dependsOn": [
                private_services_access_peering_connection_resource_creation_name,
            ],
        },
    }

    resources = [
        network_resource,
        private_services_reserved_ip_range_resource,
        vpc_access_connector_create_action,
        vpc_access_connector_delete_action,
        private_services_access_peering_connection_resource,
        cloud_sql_instance_resource,
    ]

    outputs = [
        {
            "name": "sqlConnectionName",
            "value": "$(ref." + cloud_sql_instance_resource_name + ".connectionName)",
        },
        {
            "name": "sqlInstanceUser",
            "value": db_user_name,
        },
        {
            "name": "sqlInstanceIp",
            "value": "$(ref." + cloud_sql_instance_resource_name + ".ipAddress)",
        },
        {
            "name": "dbName",
            "value": db_name,
        },
        {
            "name": "databaseUrl",
            "value": "postgres://"
            + db_user_name
            + ":<YOUR_PASSWORD>@"
            + "$(ref."
            + cloud_sql_instance_resource_name
            + ".ipAddress)"
            + ":5432/"
            + db_name
            + "?sslmode=disable",
        },
        {
            "name": "vpcAccessConnectorId",
            "value": "projects/"
            + project_id
            + "/locations/"
            + region
            + "/connectors/"
            + connector_id,
        },
    ]

    return {
        "resources": resources,
        "outputs": outputs,
    }
