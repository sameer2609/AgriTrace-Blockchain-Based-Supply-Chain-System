from solcx import compile_standard, install_solc
from web3 import Web3, EthereumTesterProvider
import json

print("=" * 60)
print("FARM TRACE BLOCKCHAIN - DEPLOYMENT SCRIPT")
print("=" * 60)

# Install Solidity compiler
print("\nInstalling Solidity compiler...")
try:
    install_solc(version='0.8.19')
    print("✓ Solidity compiler installed")
except Exception as e:
    print(f"Note: {e}")
    print("✓ Solidity compiler already installed or installed now")

# Read contract
print("\nReading contract source code...")
try:
    with open('./contracts/FarmSupplyChain.sol', 'r') as file:
        contract_source_code = file.read()
    print("✓ Contract source loaded")
except FileNotFoundError:
    print("✗ ERROR: contracts/FarmSupplyChain.sol not found!")
    print("Please create the contracts folder and add FarmSupplyChain.sol")
    exit()

# Compile contract
print("\nCompiling contract...")
try:
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"FarmSupplyChain.sol": {"content": contract_source_code}},
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                }
            },
        },
        solc_version="0.8.19",
    )
    print("✓ Contract compiled successfully")
except Exception as e:
    print(f"✗ Compilation error: {e}")
    exit()

# Save compiled contract
with open('compiled_contract.json', 'w') as file:
    json.dump(compiled_sol, file, indent=2)
print("✓ Compiled contract saved to compiled_contract.json")

# Get bytecode and ABI
bytecode = compiled_sol['contracts']['FarmSupplyChain.sol']['FarmSupplyChain']['evm']['bytecode']['object']
abi = compiled_sol['contracts']['FarmSupplyChain.sol']['FarmSupplyChain']['abi']

# Save ABI
with open('contract_abi.json', 'w') as file:
    json.dump(abi, file, indent=2)
print("✓ ABI saved to contract_abi.json")

# Connect to local blockchain (eth-tester)
print("\nConnecting to local blockchain...")
w3 = Web3(EthereumTesterProvider())
print(f"✓ Connected to blockchain")
print(f"  Chain ID: {w3.eth.chain_id}")
print(f"  Latest Block: {w3.eth.block_number}")

# Get default account
account = w3.eth.accounts[0]
balance = w3.eth.get_balance(account)
print(f"  Deployer: {account}")
print(f"  Balance: {w3.from_wei(balance, 'ether')} ETH")

# Deploy contract
print("\nDeploying contract...")
Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Contract.constructor().transact({'from': account})
print(f"  Transaction hash: {tx_hash.hex()}")

# Wait for receipt
print("  Waiting for confirmation...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("\n" + "=" * 60)
print("✓ CONTRACT DEPLOYED SUCCESSFULLY!")
print("=" * 60)
print(f"Contract Address: {tx_receipt.contractAddress}")
print(f"Block Number: {tx_receipt.blockNumber}")
print(f"Gas Used: {tx_receipt.gasUsed}")
print("=" * 60)

print("\n📝 IMPORTANT: Add these to your .env file:")
print("=" * 60)
print(f"CONTRACT_ADDRESS={tx_receipt.contractAddress}")
print(f"PRIVATE_KEY={w3.eth.accounts[0]}")
print("POLYGON_RPC_URL=http://127.0.0.1:8545")
print("PORT=5000")
print("=" * 60)

print("\n✓ Setup complete! Next steps:")
print("  1. Copy the CONTRACT_ADDRESS above")
print("  2. Add it to your .env file")
print("  3. Run: python app.py")
print("  4. Run: python customer_app.py (in new terminal)")
print("\n" + "=" * 60)