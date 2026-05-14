import oci
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List


def get_availability_domains(identity_client, compartment_id: str) -> List[str]:
    """Dynamically fetch availability domains using the provided pattern."""
    try:
        availability_domains = oci.pagination.list_call_get_all_results(
            identity_client.list_availability_domains,
            compartment_id=compartment_id
        ).data
        return [ad.name for ad in availability_domains]
    except Exception as e:
        print(f"⚠️  Could not fetch availability domains: {e}")
        return []


def get_e5_capacity(
        region: Optional[str] = None,
        compartment_id: Optional[str] = None,
        use_dynamic_ad: bool = True
) -> None:
    """
    Get E5 CPU, memory, and block storage usage/availability for a region using OCI Limits API.
    Availability Domains are now fetched dynamically as requested.
    """
    # Load OCI configuration
    try:
        config = oci.config.from_file()
        if region:
            config["region"] = region
            print(f"🔧 Overriding region to: {region}")
        else:
            print(f"📍 Using region from config: {config.get('region', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to load OCI config: {e}")
        print("Make sure you have ~/.oci/config file with valid credentials.")
        sys.exit(1)

    # Initialize clients
    limits_client = oci.limits.LimitsClient(config)
    identity_client = oci.identity.IdentityClient(config)

    # Determine compartment (default to tenancy)
    if not compartment_id:
        compartment_id = config["tenancy"]

    print(f"🏢 Tenancy OCID: {config['tenancy']}")
    print(f"📦 Using compartment: {compartment_id}")
    print(f"⏰ Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

    # Dynamically get availability domains
    ads = []
    if use_dynamic_ad:
        print("🌐 Fetching availability domains dynamically...")
        ads = get_availability_domains(identity_client, compartment_id)
        if ads:
            print(f"📍 Found availability domains: {', '.join(ads)}")
        else:
            print("⚠️  No availability domains found, will attempt queries without AD")
    else:
        print("📍 Using provided availability domain (if any)")

    # Define metrics to check - expanded from user feedback
    metrics = [
        {
            "service_name": "compute",
            "limit_name": "standard-e5-core-count",
            "display_name": "E5 CPU Cores",
            "requires_ad": True
        },
        {
            "service_name": "compute",
            "limit_name": "standard-e5-memory-count",
            "display_name": "E5 Memory (GB)",
            "requires_ad": True
        },
        {
            "service_name": "block-storage",
            "limit_name": "total-storage-gb",
            "display_name": "Block Storage Total (GB)",
            "requires_ad": True
        },
        {
            "service_name": "block-storage",
            "limit_name": "volume-count",
            "display_name": "Block Volume Count",
            "requires_ad": True
        },
    ]

    for metric in metrics:
        print(f"\n📊 {metric['display_name']}")
        print("-" * 80)

        try:
            # 1. Get limit values (as shown in user feedback)
            limit_response = limits_client.list_limit_values(
                service_name=metric["service_name"],
                name=metric["limit_name"],
                compartment_id=config["tenancy"]
            )

            # for item in limit_response.data:
            #     print(f"   • Limit Name : {item.name}")
            #     print(f"   • Limit Value: {item.value}")

            # 2. Get resource availability - per AD if needed (following user request)
            if metric["requires_ad"] and ads:
                for ad in ads:
                    print(f"   🔹 Availability Domain: {ad}")
                    availability_params: Dict[str, Any] = {
                        "service_name": metric["service_name"],
                        "limit_name": metric["limit_name"],
                        "compartment_id": compartment_id,
                        "availability_domain": ad
                    }

                    availability_response = limits_client.get_resource_availability(**availability_params)
                    data = availability_response.data

                    print(f"      • Used      : {getattr(data, 'used', 'N/A')}")
                    print(f"      • Available : {getattr(data, 'available', 'N/A')}")
                    if hasattr(data, 'effective_limit'):
                        print(f"      • Effective Limit : {data.effective_limit}")
                    print()
            else:
                # For resources that don't require AD or if no ADs found
                availability_params: Dict[str, Any] = {
                    "service_name": metric["service_name"],
                    "limit_name": metric["limit_name"],
                    "compartment_id": compartment_id,
                }

                availability_response = limits_client.get_resource_availability(**availability_params)
                data = availability_response.data

                print(f"   • Used      : {getattr(data, 'used', 'N/A')}")
                print(f"   • Available : {getattr(data, 'available', 'N/A')}")
                if hasattr(data, 'effective_limit'):
                    print(f"   • Effective Limit : {data.effective_limit}")

        except oci.exceptions.ServiceError as e:
            print(f"   ❌ Service Error: {e.message}")
            if "404" in str(e):
                print("   💡 Hint: This limit name may not exist in the current region or tenancy.")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    print("\n" + "=" * 90)
    print("✅ E5 Capacity Report Completed Successfully")
    print("💡 ADs are now fetched dynamically using IdentityClient + pagination as requested.")
    print("💡 Tip: You can still pass compartment_id as a command line argument.")


if __name__ == "__main__":
    # Command line support for region and compartment
    region = 'ap-sydney-1'
    region = 'us-ashburn-1'
    compartment = "ocid1.compartment.oc1..aaaaaaaa67aj6v3kzhmcvyddk2yi7snd4x7vo6xtfdipk7fp4g2sp7rf4a7q"

    print("🚀 OCI E5 Capacity Checker (CPU, Memory, Block Storage) - Dynamic AD Support\n")
    get_e5_capacity(
        region=region,
        compartment_id=compartment,
        use_dynamic_ad=True
    )