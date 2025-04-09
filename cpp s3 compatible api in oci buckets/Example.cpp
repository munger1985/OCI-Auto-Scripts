/// aws package is obtained by vcpkg, auto integrated with your Visual studio or cmake
#include <iostream>
#include <aws/core/Aws.h>


#include <aws/s3/S3Client.h>
#include <aws/s3/model/PutObjectRequest.h>
#include <fstream>
#include  <aws/core/auth/AWSCredentials.h>  // 凭证类所需

#include <aws/core/auth/AWSCredentialsProviderChain.h>

int main()
{
	std::cout << "Hello World!\n";

	Aws::SDKOptions options;
	Aws::InitAPI(options);
	{


		Aws::Client::ClientConfiguration config;

		config.region = "ap-singapore-1"; // Set your region
		config.endpointOverride = "https://sehubjapacprod.compat.objectstorage.AP-SINGAPORE-1.oraclecloud.com";

		Aws::Auth::AWSCredentials credentials(
			"aab8501fe123ea8958c1ee8253a",
			"ugZQuWevwme2Xmgj9W+60yq4IneE="
		);

		// first param is namespace, 2nd param is region 
		// S3 compatible URL is https://NAMESPACE.compat.objectstorage.REGION.oraclecloud.com/ 
		config.scheme = Aws::Http::Scheme::HTTP;
		config.verifySSL = true;
		// 3rd param is access key, 4th param is secret key
		Aws::S3::S3Client m_client(credentials, config,
			Aws::Client::AWSAuthV4Signer::PayloadSigningPolicy::Never, false);
		int result = 0;
		auto outcome = m_client.ListBuckets();
		if (!outcome.IsSuccess()) {
			std::cerr << "Failed with error: " << outcome.GetError() << std::endl;
			result = 1;
		}
		else {
			std::cout << "Found " << outcome.GetResult().GetBuckets().size()
				<< " buckets\n";
			for (auto& bucket : outcome.GetResult().GetBuckets()) {
				std::cout << bucket.GetName() << std::endl;
			}
		}



		Aws::S3::Model::PutObjectRequest request;
		const Aws::String& filePath = "c:/c.cc";
		const Aws::String& objectKey = "c.cc";
		const Aws::String& bucketName = "velero";
		request.SetBucket(bucketName);
		request.SetKey(filePath);
		dd();

		// Open the file
		auto inputData = Aws::MakeShared<Aws::FStream>("PutObjectInputStream",
			filePath.c_str(), std::ios_base::in | std::ios_base::binary);

		if (!inputData->is_open()) {
			//uploadFileToS3("velero", "c.cc", "C:\\c.cc");
			std::cerr << "Error opening file: " << filePath << std::endl;
			return false;
		}

		request.SetBody(inputData);

		// Upload the file
		auto outcome2 = m_client.PutObject(request);

		if (!outcome2.IsSuccess()) {
			std::cerr << "Error uploading object: " << outcome.GetError().GetMessage() << std::endl;
			return false;
		}

		std::cout << "Successfully uploaded '" << filePath << "' to S3 bucket: " << bucketName << std::endl;




	}
	// Cleanup AWS SDK

	Aws::ShutdownAPI(options);
	return 0;

}

// Run program: Ctrl + F5 or Debug > Start Without Debugging menu
// Debug program: F5 or Debug > Start Debugging menu

// Tips for Getting Started: 
//   1. Use the Solution Explorer window to add/manage files
//   2. Use the Team Explorer window to connect to source control
//   3. Use the Output window to see build output and other messages
//   4. Use the Error List window to view errors
//   5. Go to Project > Add New Item to create new code files, or Project > Add Existing Item to add existing code files to the project
//   6. In the future, to open this project again, go to File > Open > Project and select the .sln file
