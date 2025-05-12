from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class KeyVaultHelper:
    def __init__(self, key_vault_name: str):
        """
        Initialize the KeyVaultHelper with the Key Vault name.
        :param key_vault_name: Name of the Azure Key Vault.
        """
        self.key_vault_url = f"https://{key_vault_name}.vault.azure.net/"
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=self.key_vault_url, credential=self.credential)

    def get_secret(self, secret_name: str) -> str:
        """
        Retrieve a secret value from Azure Key Vault.
        :param secret_name: Name of the secret in Key Vault.
        :return: The value of the secret.
        """
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve secret '{secret_name}' from Key Vault: {e}")
