
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
from web3 import Web3, EthereumTesterProvider
from solcx import compile_standard, install_solc
from datetime import datetime
import json
import threading
import qrcode
import os
from io import BytesIO

print("=" * 60)
print("FARM TRACE - COMPLETE SYSTEM WITH QR CODE")
print("=" * 60)

# Create QR codes directory
QR_CODE_DIR = './qr_codes'
if not os.path.exists(QR_CODE_DIR):
    os.makedirs(QR_CODE_DIR)
    print(f"✓ Created QR codes directory: {QR_CODE_DIR}")

# Create contracts directory  
CONTRACTS_DIR = './contracts'
if not os.path.exists(CONTRACTS_DIR):
    os.makedirs(CONTRACTS_DIR)
    print(f"✓ Created contracts directory: {CONTRACTS_DIR}")

# Create contract file
CONTRACT_FILE = os.path.join(CONTRACTS_DIR, 'FarmSupplyChain.sol')
if not os.path.exists(CONTRACT_FILE):
    with open(CONTRACT_FILE, 'w') as cf:
        cf.write(open(CONTRACT_FILE,'r').read() if os.path.exists(CONTRACT_FILE) else '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
contract FarmSupplyChain {
    enum Stage { Harvested, InWarehouse, InTransit, AtDistributor, AtRetailer, Sold }
    struct Product { string productId; string productName; string variety; uint256 quantity; string qualityGrade; address farmer; string farmLocation; uint256 harvestDate; Stage currentStage; bool exists; }
    struct StageUpdate { address handler; string handlerName; Stage stage; string location; string temperature; string humidity; uint256 timestamp; string notes; }
    mapping(string => Product) public products;
    mapping(string => StageUpdate[]) public productHistory;
    string[] public productIds;
    event ProductRegistered(string indexed productId, address indexed farmer, uint256 timestamp);
    event ProductUpdated(string indexed productId, Stage stage, address indexed handler, uint256 timestamp);
    function registerProduct(string memory _productId, string memory _productName, string memory _variety, uint256 _quantity, string memory _qualityGrade, string memory _farmLocation, string memory _temperature, string memory _humidity, string memory _farmerName, string memory _notes) public { require(!products[_productId].exists, "Product already exists"); products[_productId] = Product(_productId, _productName, _variety, _quantity, _qualityGrade, msg.sender, _farmLocation, block.timestamp, Stage.Harvested, true); productIds.push(_productId); productHistory[_productId].push(StageUpdate(msg.sender, _farmerName, Stage.Harvested, _farmLocation, _temperature, _humidity, block.timestamp, _notes)); emit ProductRegistered(_productId, msg.sender, block.timestamp); }
    function updateProduct(string memory _productId, Stage _stage, string memory _location, string memory _temperature, string memory _humidity, string memory _handlerName, string memory _notes) public { require(products[_productId].exists, "Product does not exist"); products[_productId].currentStage = _stage; productHistory[_productId].push(StageUpdate(msg.sender, _handlerName, _stage, _location, _temperature, _humidity, block.timestamp, _notes)); emit ProductUpdated(_productId, _stage, msg.sender, block.timestamp); }
    function getProduct(string memory _productId) public view returns (string memory productName, string memory variety, uint256 quantity, string memory qualityGrade, address farmer, string memory farmLocation, uint256 harvestDate, Stage currentStage) { Product memory p = products[_productId]; return (p.productName, p.variety, p.quantity, p.qualityGrade, p.farmer, p.farmLocation, p.harvestDate, p.currentStage); }
    function getProductHistory(string memory _productId) public view returns (StageUpdate[] memory) { return productHistory[_productId]; }
    function productExistsCheck(string memory _productId) public view returns (bool) { return products[_productId].exists; }
}''')


# Install and compile
print("\n1. Installing Solidity compiler...")
install_solc(version='0.8.19')

print("2. Reading and compiling contract...")
with open(CONTRACT_FILE, 'r') as file:
    contract_source = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"FarmSupplyChain.sol": {"content": contract_source}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "evm.bytecode"]}
            }
        },
    },
    solc_version="0.8.19",
)

bytecode = compiled_sol['contracts']['FarmSupplyChain.sol']['FarmSupplyChain']['evm']['bytecode']['object']
abi = compiled_sol['contracts']['FarmSupplyChain.sol']['FarmSupplyChain']['abi']

# Deploy to shared blockchain
print("3. Deploying contract...")
w3 = Web3(EthereumTesterProvider())
account = w3.eth.accounts[0]

Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
tx_hash = Contract.constructor().transact({'from': account})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = tx_receipt.contractAddress

contract = w3.eth.contract(address=contract_address, abi=abi)

print(f"✓ Contract deployed at: {contract_address}")

STAGES = ['Harvested', 'In Warehouse', 'In Transit', 'At Distributor', 'At Retailer', 'Sold']

# Tamil Nadu locations
TAMIL_NADU_LOCATIONS = [
    'Chennai',
    'Coimbatore',
    'Madurai',
    'Tiruchirappalli',
    'Salem',
    'Tirunelveli',
    'Erode',
    'Vellore',
    'Thoothukudi',
    'Thanjavur',
    'Dindigul',
    'Kanchipuram',
    'Karur',
    'Rajapalayam',
    'Nagercoil',
    'Kumbakonam',
    'Tiruppur',
    'Cuddalore',
    'Pollachi',
    'Kanyakumari'
]

# Banana varieties
BANANA_VARIETIES = [
    'Robusta (Poovan)',
    'Nendran',
    'Red Banana',
    'Rasthali',
    'Karpuravalli',
    'Monthan',
    'Yelakki',
    'Grand Naine',
    'Cavendish',
    'Pachanadan'
]

def generate_qr_code(product_id):
    """Generate QR code for product ID and save to local directory"""
    try:
        # Create QR code with tracking URL
        tracking_url = f"http://localhost:5001/?id={product_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(tracking_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_filename = f"{product_id}.png"
        qr_filepath = os.path.join(QR_CODE_DIR, qr_filename)
        img.save(qr_filepath)
        
        print(f"✓ QR code generated: {qr_filepath}")
        return qr_filepath
    except Exception as e:
        print(f"✗ Error generating QR code: {str(e)}")
        return None

# ============== BACKEND APP (For Staff) ==============
backend_app = Flask(__name__)
CORS(backend_app)

@backend_app.route('/')
def backend_home():
    return render_template_string(BACKEND_HTML)

@backend_app.route('/api/products/register', methods=['POST'])
def register_product():
    """Register new product and generate QR code"""
    try:
        data = request.json
        product_id = data.get('productId', '')
        
        tx_hash = contract.functions.registerProduct(
            product_id,
            data.get('productName', 'Banana'),
            data.get('variety', ''),
            int(data.get('quantity', 0)),
            data.get('qualityGrade', ''),
            data.get('farmLocation', ''),
            data.get('temperature', ''),
            data.get('humidity', ''),
            data.get('farmerName', ''),
            data.get('notes', '')
        ).transact({'from': account})
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Generate QR code
        qr_path = generate_qr_code(product_id)
        
        return jsonify({
            'success': True,
            'productId': product_id,
            'transactionHash': tx_hash.hex(),
            'blockNumber': receipt['blockNumber'],
            'qrCodePath': qr_path,
            'qrCodeUrl': f'/api/qrcode/{product_id}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@backend_app.route('/api/qrcode/<product_id>', methods=['GET'])
def get_qr_code(product_id):
    """Retrieve QR code image"""
    try:
        qr_filepath = os.path.join(QR_CODE_DIR, f"{product_id}.png")
        if os.path.exists(qr_filepath):
            return send_file(qr_filepath, mimetype='image/png')
        else:
            return jsonify({'success': False, 'error': 'QR code not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@backend_app.route('/api/products/update', methods=['POST'])
def update_product():
    """Update product stage"""
    try:
        data = request.json
        tx_hash = contract.functions.updateProduct(
            data.get('productId', ''),
            int(data.get('stage', 0)),
            data.get('location', ''),
            data.get('temperature', ''),
            data.get('humidity', ''),
            data.get('handlerName', ''),
            data.get('notes', '')
        ).transact({'from': account})
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return jsonify({
            'success': True,
            'transactionHash': tx_hash.hex(),
            'blockNumber': receipt['blockNumber']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@backend_app.route('/api/products/<product_id>', methods=['GET'])
def get_product_backend(product_id):
    """Get product details for backend"""
    try:
        exists = contract.functions.productExistsCheck(product_id).call()
        if not exists:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        product = contract.functions.getProduct(product_id).call()
        history_data = contract.functions.getProductHistory(product_id).call()
        
        # --- NEW: Get event logs to find transaction hashes ---
        # 1. Get registration event
        register_event_filter = contract.events.ProductRegistered.create_filter(
            from_block=0,  # <-- FIXED
            argument_filters={'productId': product_id}
        )
        register_logs = register_event_filter.get_all_entries()
        
        # 2. Get update events
        update_event_filter = contract.events.ProductUpdated.create_filter(
            from_block=0,  # <-- FIXED
            argument_filters={'productId': product_id}
        )
        update_logs = update_event_filter.get_all_entries()

        # 3. Create a lookup map for hash by timestamp
        hash_by_timestamp = {}
        for log in register_logs + update_logs:
            hash_by_timestamp[log['args']['timestamp']] = log['transactionHash'].hex()
        # --- END NEW ---
        
        product_data = {
            'productId': product_id,
            'productName': product[0],
            'variety': product[1],
            'quantity': str(product[2]),
            'qualityGrade': product[3],
            'farmer': product[4],
            'farmLocation': product[5],
            'harvestDate': datetime.fromtimestamp(product[6]).strftime('%Y-%m-%d %H:%M:%S'),
            'currentStage': STAGES[product[7]],
            'currentStageIndex': product[7],
            'qrCodeUrl': f'/api/qrcode/{product_id}',
            'history': [
                {
                    'handler': h[0],
                    'handlerName': h[1],
                    'stage': STAGES[h[2]],
                    'location': h[3],
                    'temperature': h[4],
                    'humidity': h[5],
                    'timestamp': datetime.fromtimestamp(h[6]).strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': h[7],
                    'transactionHash': hash_by_timestamp.get(h[6], 'N/A') # <-- ADDED HASH
                }
                for h in history_data
            ]
        }
        
        return jsonify({'success': True, 'product': product_data})
    except Exception as e:
        print(f"Error in get_product_backend: {e}") # Added print for debugging
        return jsonify({'success': False, 'error': str(e)}), 500

@backend_app.route('/api/health', methods=['GET'])
def health_backend():
    return jsonify({
        'status': 'OK',
        'contract': contract_address,
        'blockNumber': w3.eth.block_number,
        'account': account
    })

# ============== CUSTOMER APP ==============
customer_app = Flask(__name__)
CORS(customer_app)

@customer_app.route('/')
def customer_home():
    return render_template_string(CUSTOMER_HTML)

@customer_app.route('/api/track/<product_id>', methods=['GET'])
def track_product(product_id):
    """Track product - Customer view"""
    try:
        exists = contract.functions.productExistsCheck(product_id).call()
        if not exists:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        product = contract.functions.getProduct(product_id).call()
        history_data = contract.functions.getProductHistory(product_id).call()
        
        # --- NEW: Get event logs to find transaction hashes ---
        # 1. Get registration event
        register_event_filter = contract.events.ProductRegistered.create_filter(
            from_block=0,  # <-- FIXED
            argument_filters={'productId': product_id}
        )
        register_logs = register_event_filter.get_all_entries()
        
        # 2. Get update events
        update_event_filter = contract.events.ProductUpdated.create_filter(
            from_block=0,  # <-- FIXED
            argument_filters={'productId': product_id}
        )
        update_logs = update_event_filter.get_all_entries()

        # 3. Create a lookup map for hash by timestamp
        hash_by_timestamp = {}
        for log in register_logs + update_logs:
            hash_by_timestamp[log['args']['timestamp']] = log['transactionHash'].hex()
        # --- END NEW ---
        
        product_data = {
            'productId': product_id,
            'productName': product[0],
            'variety': product[1],
            'quantity': str(product[2]),
            'qualityGrade': product[3],
            'farmer': product[4],
            'farmLocation': product[5],
            'harvestDate': datetime.fromtimestamp(product[6]).strftime('%Y-%m-%d %H:%M:%S'),
            'currentStage': STAGES[product[7]],
            'history': [
                {
                    'handler': h[0],
                    'handlerName': h[1],
                    'stage': STAGES[h[2]],
                    'location': h[3],
                    'temperature': h[4],
                    'humidity': h[5],
                    'timestamp': datetime.fromtimestamp(h[6]).strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': h[7],
                    'transactionHash': hash_by_timestamp.get(h[6], 'N/A') # <-- ADDED HASH
                }
                for h in history_data
            ]
        }
        
        return jsonify({'success': True, 'product': product_data})
    except Exception as e:
        print(f"Error in track_product: {e}") # Added print for debugging
        return jsonify({'success': False, 'error': str(e)}), 500

@customer_app.route('/api/health', methods=['GET'])
def health_customer():
    return jsonify({
        'status': 'OK',
        'contract': contract_address,
        'blockNumber': w3.eth.block_number
    })

# ============== HTML TEMPLATES ==============
BACKEND_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farm Supply Chain Management</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-7xl mx-auto p-6">
        <header class="bg-gradient-to-r from-green-600 to-blue-600 text-white p-8 rounded-lg shadow-xl mb-8">
            <h1 class="text-4xl font-bold flex items-center gap-3">
                <i class="fas fa-tractor"></i>
                Farm Supply Chain Management
            </h1>
            <p class="mt-2 text-green-100">Complete product lifecycle tracking on blockchain</p>
        </header>

        <div class="grid md:grid-cols-2 gap-8">
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                    <i class="fas fa-plus-circle text-green-600"></i>
                    Register New Product
                </h2>
                
                <form id="registerForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Product ID *</label>
                        <input type="text" id="productId" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="e.g., BANANA-001">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Product Name *</label>
                        <input type="text" id="productName" value="Banana" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-gray-50"
                            readonly>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Banana Variety *</label>
                        <select id="variety" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            ''' + ''.join([f'<option value="{variety}">{variety}</option>' for variety in BANANA_VARIETIES]) + '''
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Quantity (kg) *</label>
                        <input type="number" id="quantity" required min="1"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="100">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Quality Grade *</label>
                        <select id="qualityGrade" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            <option value="A+">A+ (Premium)</option>
                            <option value="A">A (Excellent)</option>
                            <option value="B">B (Good)</option>
                            <option value="C">C (Standard)</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Farm Location (Tamil Nadu) *</label>
                        <select id="farmLocation" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            ''' + ''.join([f'<option value="{location}">{location}</option>' for location in TAMIL_NADU_LOCATIONS]) + '''
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Temperature</label>
                        <input type="text" id="temperature"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="e.g., 25°C">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Humidity</label>
                        <input type="text" id="humidity"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="e.g., 60%">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Farmer Name *</label>
                        <input type="text" id="farmerName" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Full name">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Notes</label>
                        <textarea id="registerNotes" rows="3"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Additional information"></textarea>
                    </div>
                    
                    <button type="submit"
                        class="w-full bg-gradient-to-r from-green-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105 shadow-lg">
                        <i class="fas fa-check-circle mr-2"></i>Register Product & Generate QR Code
                    </button>
                </form>

                <div id="registerResult" class="mt-4 hidden"></div>
                <div id="qrCodeDisplay" class="mt-4 hidden"></div>
            </div>

            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                    <i class="fas fa-edit text-blue-600"></i>
                    Update Product Stage
                </h2>
                
                <form id="updateForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Product ID *</label>
                        <input type="text" id="updateProductId" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., BANANA-001">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Stage *</label>
                        <select id="stage" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="0">Harvested</option>
                            <option value="1">In Warehouse</option>
                            <option value="2">In Transit</option>
                            <option value="3">At Distributor</option>
                            <option value="4">At Retailer</option>
                            <option value="5">Sold</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Location (Tamil Nadu)</label>
                        <select id="updateLocation"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="">-- Select Location --</option>
                            ''' + ''.join([f'<option value="{location}">{location}</option>' for location in TAMIL_NADU_LOCATIONS]) + '''
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Temperature</label>
                        <input type="text" id="updateTemperature"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., 25°C">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Humidity</label>
                        <input type="text" id="updateHumidity"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="e.g., 60%">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Handler Name *</label>
                        <input type="text" id="handlerName" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Full name">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Notes</label>
                        <textarea id="updateNotes" rows="3"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Update details"></textarea>
                    </div>
                    
                    <button type="submit"
                        class="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg">
                        <i class="fas fa-sync-alt mr-2"></i>Update Stage
                    </button>
                </form>

                <div id="updateResult" class="mt-4 hidden"></div>
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-lg p-6 mt-8">
            <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <i class="fas fa-search text-purple-600"></i>
                Search Product
            </h2>
            
            <div class="flex gap-4">
                <input type="text" id="searchProductId"
                    class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="Enter Product ID">
                <button onclick="searchProduct()"
                    class="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg">
                    <i class="fas fa-search mr-2"></i>Search
                </button>
            </div>

            <div id="searchResult" class="mt-6 hidden"></div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;

        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const resultDiv = document.getElementById('registerResult');
            const qrDiv = document.getElementById('qrCodeDisplay');
            resultDiv.className = 'mt-4 p-4 rounded-lg';
            resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Registering product and generating QR code...';
            resultDiv.classList.remove('hidden');
            qrDiv.classList.add('hidden');
            
            try {
                const response = await fetch(`${API_URL}/api/products/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        productId: document.getElementById('productId').value.trim().toUpperCase(),
                        productName: document.getElementById('productName').value,
                        variety: document.getElementById('variety').value,
                        quantity: document.getElementById('quantity').value,
                        qualityGrade: document.getElementById('qualityGrade').value,
                        farmLocation: document.getElementById('farmLocation').value,
                        temperature: document.getElementById('temperature').value,
                        humidity: document.getElementById('humidity').value,
                        farmerName: document.getElementById('farmerName').value,
                        notes: document.getElementById('registerNotes').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.className = 'mt-4 p-4 bg-green-50 border-2 border-green-500 rounded-lg';
                    resultDiv.innerHTML = `
                        <div class="flex items-start gap-3">
                            <i class="fas fa-check-circle text-green-600 text-2xl mt-1"></i>
                            <div class="flex-1">
                                <p class="font-bold text-green-800 text-lg mb-2">Product Registered Successfully!</p>
                                <p class="text-sm text-gray-700"><strong>Product ID:</strong> ${data.productId}</p>
                                <div class="bg-white p-3 rounded-lg mb-2">
                                    <p class="text-sm text-gray-600 mb-1">Transaction Hash</p>
                                    <p class="text-xs font-mono bg-gray-50 p-2 rounded break-all text-blue-600">${data.transactionHash}</p>
                                </div>
                                <p class="text-sm text-gray-700"><strong>Block:</strong> ${data.blockNumber}</p>
                                <p class="text-sm text-green-700 mt-2"><strong>QR Code Generated!</strong> See below.</p>
                            </div>
                        </div>
                    `;

                    // Display QR Code
                    qrDiv.className = 'mt-4 p-6 bg-blue-50 border-2 border-blue-500 rounded-lg text-center';
                    qrDiv.innerHTML = `
                        <h3 class="text-xl font-bold text-blue-800 mb-4">
                            <i class="fas fa-qrcode mr-2"></i>QR Code Generated
                        </h3>
                        <img src="${data.qrCodeUrl}" alt="QR Code" class="mx-auto border-4 border-white shadow-lg rounded-lg mb-4" style="max-width: 300px;">
                        <p class="text-sm text-gray-700 mb-2">Scan this QR code to track the product</p>
                        <a href="${data.qrCodeUrl}" download="${data.productId}.png" 
                           class="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all">
                            <i class="fas fa-download mr-2"></i>Download QR Code
                        </a>
                    `;
                    qrDiv.classList.remove('hidden');
                    
                    document.getElementById('registerForm').reset();
                    document.getElementById('productName').value = 'Banana';
                } else {
                    resultDiv.className = 'mt-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg';
                    resultDiv.innerHTML = `
                        <div class="flex items-start gap-3">
                            <i class="fas fa-times-circle text-red-600 text-2xl mt-1"></i>
                            <div>
                                <p class="font-bold text-red-800">Error</p>
                                <p class="text-sm text-gray-700">${data.error}</p>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.className = 'mt-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg';
                resultDiv.innerHTML = `
                    <div class="flex items-start gap-3">
                        <i class="fas fa-exclamation-triangle text-red-600 text-2xl mt-1"></i>
                        <div>
                            <p class="font-bold text-red-800">Connection Error</p>
                            <p class="text-sm text-gray-700">${error.message}</p>
                        </div>
                    </div>
                `;
            }
        });

        document.getElementById('updateForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const resultDiv = document.getElementById('updateResult');
            resultDiv.className = 'mt-4 p-4 rounded-lg';
            resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Updating product...';
            resultDiv.classList.remove('hidden');
            
            try {
                const response = await fetch(`${API_URL}/api/products/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        productId: document.getElementById('updateProductId').value.trim().toUpperCase(),
                        stage: document.getElementById('stage').value,
                        location: document.getElementById('updateLocation').value,
                        temperature: document.getElementById('updateTemperature').value,
                        humidity: document.getElementById('updateHumidity').value,
                        handlerName: document.getElementById('handlerName').value,
                        notes: document.getElementById('updateNotes').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.className = 'mt-4 p-4 bg-green-50 border-2 border-green-500 rounded-lg';
                    resultDiv.innerHTML = `
                        <div class="flex items-start gap-3">
                            <i class="fas fa-check-circle text-green-600 text-2xl mt-1"></i>
                            <div>
                                <p class="font-bold text-green-800 text-lg">Update Successful!</p>
                                <div class="bg-white p-3 rounded-lg mb-2">
                                    <p class="text-sm text-gray-600 mb-1">Transaction Hash</p>
                                    <p class="text-xs font-mono bg-gray-50 p-2 rounded break-all text-blue-600">${data.transactionHash}</p>
                                </div>
                                <p class="text-sm text-gray-700"><strong>Block:</strong> ${data.blockNumber}</p>
                            </div>
                        </div>
                    `;
                    document.getElementById('updateForm').reset();
                } else {
                    resultDiv.className = 'mt-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg';
                    resultDiv.innerHTML = `
                        <div class="flex items-start gap-3">
                            <i class="fas fa-times-circle text-red-600 text-2xl mt-1"></i>
                            <div>
                                <p class="font-bold text-red-800">Error</p>
                                <p class="text-sm text-gray-700">${data.error}</p>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.className = 'mt-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg';
                resultDiv.innerHTML = `
                    <div class="flex items-start gap-3">
                        <i class="fas fa-exclamation-triangle text-red-600 text-2xl mt-1"></i>
                        <div>
                            <p class="font-bold text-red-800">Connection Error</p>
                            <p class="text-sm text-gray-700">${error.message}</p>
                        </div>
                    </div>
                `;
            }
        });

        async function searchProduct() {
            const productId = document.getElementById('searchProductId').value.trim().toUpperCase();
            const resultDiv = document.getElementById('searchResult');
            
            if (!productId) {
                resultDiv.className = 'mt-6 p-4 bg-yellow-50 border-2 border-yellow-500 rounded-lg';
                resultDiv.innerHTML = '<p class="text-yellow-800">Please enter a Product ID</p>';
                resultDiv.classList.remove('hidden');
                return;
            }
            
            resultDiv.className = 'mt-6 p-4 rounded-lg';
            resultDiv.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Searching...';
            resultDiv.classList.remove('hidden');
            
            try {
                const response = await fetch(`${API_URL}/api/products/${productId}`);
                const data = await response.json();
                
                if (data.success) {
                    const product = data.product;
                    resultDiv.className = 'mt-6 p-6 bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-300 rounded-lg';
                    resultDiv.innerHTML = `
                        <h3 class="text-2xl font-bold text-gray-800 mb-4">${product.productName}</h3>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            <div class="bg-white p-4 rounded-lg shadow">
                                <p class="text-sm text-gray-600">Product ID</p>
                                <p class="text-lg font-bold text-gray-800">${product.productId}</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow">
                                <p class="text-sm text-gray-600">Variety</p>
                                <p class="text-lg font-bold text-gray-800">${product.variety}</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow">
                                <p class="text-sm text-gray-600">Quantity</p>
                                <p class="text-lg font-bold text-gray-800">${product.quantity} kg</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow">
                                <p class="text-sm text-gray-600">Quality Grade</p>
                                <p class="text-lg font-bold text-green-600">${product.qualityGrade}</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow">
                                <p class="text-sm text-gray-600">Farm Location</p>
                                <p class="text-lg font-bold text-gray-800">${product.farmLocation}</p>
                            </div>
                            <div class="bg-white p-4 rounded-lg shadow">
                                <p class="text-sm text-gray-600">Current Stage</p>
                                <p class="text-lg font-bold text-blue-600">${product.currentStage}</p>
                            </div>
                        </div>
                        
                        <div class="bg-white p-6 rounded-lg shadow-lg mb-4">
                            <h4 class="text-xl font-bold text-gray-800 mb-4">
                                <i class="fas fa-qrcode mr-2 text-blue-600"></i>QR Code
                            </h4>
                            <img src="${product.qrCodeUrl}" alt="QR Code" class="mx-auto border-4 border-gray-200 rounded-lg shadow-md" style="max-width: 250px;">
                            <div class="text-center mt-4">
                                <a href="${product.qrCodeUrl}" download="${product.productId}.png" 
                                   class="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all">
                                    <i class="fas fa-download mr-2"></i>Download QR Code
                                </a>
                            </div>
                        </div>
                        
                        <div class="bg-white p-4 rounded-lg shadow">
                            <h4 class="text-lg font-bold text-gray-800 mb-3">Product History</h4>
                            <div class="space-y-3">
                                ${product.history.map((h, i) => `
                                    <div class="border-l-4 border-purple-500 pl-4 py-2 bg-gray-50 rounded-r-lg">
                                        <p class="font-bold text-gray-800">${i + 1}. ${h.stage}</p>
                                        <p class="text-sm text-gray-600">Handler: ${h.handlerName}</p>
                                        <p class="text-sm text-gray-600">Location: ${h.location}</p>
                                        <p class="text-sm text-gray-600">Time: ${h.timestamp}</p>
                                        ${h.notes ? `<p class="text-sm text-gray-600 italic">Notes: ${h.notes}</p>` : ''}
                                        <div class="mt-2">
                                            <p class="text-xs text-gray-500">Transaction Hash</p>
                                            <p class="text-xs font-mono bg-gray-100 p-1 rounded break-all text-blue-600">${h.transactionHash}</p>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                } else {
                    resultDiv.className = 'mt-6 p-4 bg-red-50 border-2 border-red-500 rounded-lg';
                    resultDiv.innerHTML = `
                        <div class="flex items-start gap-3">
                            <i class="fas fa-times-circle text-red-600 text-2xl mt-1"></i>
                            <div>
                                <p class="font-bold text-red-800">Product Not Found</p>
                                <p class="text-sm text-gray-700">${data.error}</p>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.className = 'mt-6 p-4 bg-red-50 border-2 border-red-500 rounded-lg';
                resultDiv.innerHTML = `
                    <div class="flex items-start gap-3">
                        <i class="fas fa-exclamation-triangle text-red-600 text-2xl mt-1"></i>
                        <div>
                            <p class="font-bold text-red-800">Connection Error</p>
                            <p class="text-sm text-gray-700">${error.message}</p>
                        </div>
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
'''

CUSTOMER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Track Your Product - Farm Supply Chain</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
</head>
<body class="bg-gradient-to-br from-green-50 to-blue-50 min-h-screen">
    <div class="max-w-6xl mx-auto p-4 md:p-8">
        <header class="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6 md:p-10 rounded-2xl shadow-2xl mb-8 text-center">
            <h1 class="text-3xl md:text-5xl font-bold mb-3 flex items-center justify-center gap-3">
                <i class="fas fa-leaf"></i>
                Farm Supply Chain Tracker
            </h1>
            <p class="text-base md:text-xl text-green-100">Verify your product's journey from farm to table</p>
        </header>

        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-8">
            <h3 class="text-xl font-bold text-gray-800 mb-4 text-center">Enter Product ID or Scan QR Code</h3>
            
            <div class="flex flex-col md:flex-row gap-4 items-center mb-6">
                <input type="text" id="searchId" 
                    class="flex-1 px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-green-500 focus:border-green-500 transition-all"
                    placeholder="Enter Product ID (e.g., BANANA-001)">
                <button onclick="searchProduct()"
                    class="w-full md:w-auto px-8 py-4 bg-gradient-to-r from-green-600 to-blue-600 text-white text-lg font-bold rounded-xl hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105 shadow-lg">
                    <i class="fas fa-search mr-2"></i>Track Product
                </button>
                <button onclick="resetSearch()"
                    class="w-full md:w-auto px-8 py-4 bg-gray-500 text-white text-lg font-bold rounded-xl hover:bg-gray-600 transition-all shadow-lg">
                    <i class="fas fa-redo mr-2"></i>Reset
                </button>
            </div>

            <div class="text-center flex flex-col md:flex-row gap-4 justify-center items-center">
                <button onclick="toggleScanner()" id="scannerToggleBtn"
                    class="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-lg font-bold rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 shadow-lg">
                    <i class="fas fa-qrcode mr-2"></i>Scan QR Code
                </button>
                
                <label for="qrUpload" class="cursor-pointer px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-lg font-bold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all transform hover:scale-105 shadow-lg inline-block">
                    <i class="fas fa-upload mr-2"></i>Upload QR
                </label>
                <input type="file" id="qrUpload" accept="image/*" class="hidden" onchange="uploadQR(event)">
            </div>

            <div id="qr-reader-upload" style="display:none;"></div>

            <div id="scanner-container" class="hidden mt-6">
                <div class="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-xl border-2 border-purple-300">
                    <div class="flex justify-between items-center mb-4">
                        <h4 class="text-lg font-bold text-gray-800">
                            <i class="fas fa-camera mr-2 text-purple-600"></i>Scanner Active
                        </h4>
                        <button onclick="stopScanner()" 
                            class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all">
                            <i class="fas fa-times mr-2"></i>Close Scanner
                        </button>
                    </div>
                    
                    <div id="reader" class="rounded-lg overflow-hidden shadow-lg border-4 border-white"></div>
                    
                    <div id="scanner-status" class="mt-4 p-3 bg-blue-100 text-blue-800 rounded-lg text-center hidden">
                        <i class="fas fa-info-circle mr-2"></i>
                        <span id="scanner-status-text">Position the QR code or barcode within the frame</span>
                    </div>
                </div>
            </div>
        </div>

        <div id="loading" class="hidden text-center py-12">
            <i class="fas fa-spinner fa-spin text-6xl text-green-600 mb-4"></i>
            <p class="text-xl text-gray-700">Loading product information...</p>
        </div>

        <div id="error-message" class="hidden bg-red-50 border-2 border-red-500 rounded-2xl p-6 mb-8">
            <div class="flex items-start gap-4">
                <i class="fas fa-exclamation-circle text-red-600 text-3xl mt-1"></i>
                <div>
                    <h3 class="text-xl font-bold text-red-800 mb-2">Error</h3>
                    <p id="error-text" class="text-gray-700"></p>
                </div>
            </div>
        </div>

        <div id="product-details-container" class="hidden space-y-8">
            <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8">
                <h2 class="text-2xl md:text-3xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <i class="fas fa-info-circle text-green-600"></i>
                    Product Information
                </h2>
                <div id="product-info"></div>
            </div>

            <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8">
                <h2 class="text-2xl md:text-3xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <i class="fas fa-history text-blue-600"></i>
                    Supply Chain Journey
                </h2>
                <div id="product-history"></div>
            </div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        let html5QrcodeScanner = null;

        // Check for product ID in URL parameters
        window.addEventListener('DOMContentLoaded', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const productId = urlParams.get('id');
            if (productId) {
                document.getElementById('searchId').value = productId;
                searchProduct();
            }
        });

        function toggleScanner() {
            const container = document.getElementById('scanner-container');
            const button = document.getElementById('scannerToggleBtn');
            
            if (container.classList.contains('hidden')) {
                startScanner();
            } else {
                stopScanner();
            }
        }

        function startScanner() {
            const container = document.getElementById('scanner-container');
            const button = document.getElementById('scannerToggleBtn');
            const statusDiv = document.getElementById('scanner-status');
            
            container.classList.remove('hidden');
            statusDiv.classList.remove('hidden');
            button.innerHTML = '<i class="fas fa-times mr-2"></i>Close Scanner';
            
            // Initialize scanner with support for both QR codes and barcodes
            html5QrcodeScanner = new Html5Qrcode("reader");
            
            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0,
                formatsToSupport: [
                    Html5QrcodeSupportedFormats.QR_CODE,
                    Html5QrcodeSupportedFormats.EAN_13,
                    Html5QrcodeSupportedFormats.EAN_8,
                    Html5QrcodeSupportedFormats.CODE_128,
                    Html5QrcodeSupportedFormats.CODE_39,
                    Html5QrcodeSupportedFormats.UPC_A,
                    Html5QrcodeSupportedFormats.UPC_E
                ]
            };
            
            html5QrcodeScanner.start(
                { facingMode: "environment" },
                config,
                onScanSuccess,
                onScanError
            ).catch(err => {
                console.error('Scanner start error:', err);
                showScannerStatus('Error starting camera. Please ensure camera permissions are granted.', 'error');
            });
        }

        function stopScanner() {
            const container = document.getElementById('scanner-container');
            const button = document.getElementById('scannerToggleBtn');
            const statusDiv = document.getElementById('scanner-status');
            
            if (html5QrcodeScanner) {
                html5QrcodeScanner.stop().then(() => {
                    html5QrcodeScanner.clear();
                    html5QrcodeScanner = null;
                }).catch(err => {
                    console.error('Error stopping scanner:', err);
                });
            }
            
            container.classList.add('hidden');
            statusDiv.classList.add('hidden');
            button.innerHTML = '<i class="fas fa-qrcode mr-2"></i>Scan QR Code / Barcode';
        }

        function onScanSuccess(decodedText, decodedResult) {
            console.log('Scan successful:', decodedText);
            showScannerStatus('Scan successful! Processing...', 'success');
            
            // Extract product ID from URL if it's a full URL, otherwise use as-is
            let productId = decodedText;
            
            // Check if it's a URL with product ID parameter
            try {
                const url = new URL(decodedText);
                const urlProductId = url.searchParams.get('id');
                if (urlProductId) {
                    productId = urlProductId;
                }
            } catch (e) {
                // Not a URL, use the text directly
                productId = decodedText;
            }
            
            // Set the product ID and search
            document.getElementById('searchId').value = productId.toUpperCase();
            
            // Stop scanner and search
            stopScanner();
            setTimeout(() => {
                searchProduct();
            }, 500);
        }

        function onScanError(errorMessage) {
            // Ignore frequent scanning errors (these are normal when no code is in view)
            // console.log('Scan error:', errorMessage);
        }

        function showScannerStatus(message, type = 'info') {
            const statusDiv = document.getElementById('scanner-status');
            const statusText = document.getElementById('scanner-status-text');
            
            statusText.textContent = message;
            statusDiv.classList.remove('hidden', 'bg-blue-100', 'text-blue-800', 'bg-green-100', 'text-green-800', 'bg-red-100', 'text-red-800');
            
            if (type === 'success') {
                statusDiv.classList.add('bg-green-100', 'text-green-800');
            } else if (type === 'error') {
                statusDiv.classList.add('bg-red-100', 'text-red-800');
            } else {
                statusDiv.classList.add('bg-blue-100', 'text-blue-800');
            }
        }

        function resetSearch() {
            document.getElementById('searchId').value = '';
            document.getElementById('product-details-container').classList.add('hidden');
            document.getElementById('error-message').classList.add('hidden');
            document.getElementById('loading').classList.add('hidden');
            stopScanner();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        async function uploadQR(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('product-details-container').classList.add('hidden');
            document.getElementById('error-message').classList.add('hidden');
            
            try {
                const html5QrCode = new Html5Qrcode("qr-reader-upload");
                const decodedText = await html5QrCode.scanFile(file, true);
                
                let productId = decodedText;
                try {
                    const url = new URL(decodedText);
                    const urlProductId = url.searchParams.get('id');
                    if (urlProductId) productId = urlProductId;
                } catch (e) {
                    productId = decodedText;
                }
                
                document.getElementById('searchId').value = productId.toUpperCase();
                document.getElementById('loading').classList.add('hidden');
                event.target.value = '';
                
                setTimeout(() => searchProduct(), 300);
            } catch (err) {
                console.error('QR scan error:', err);
                document.getElementById('loading').classList.add('hidden');
                showError('Failed to read QR code. Please ensure the image contains a valid QR code.');
                event.target.value = '';
            }
        }

        async function searchProduct() {
            const productId = document.getElementById('searchId').value.trim().toUpperCase();
            
            if (!productId) {
                showError('Please enter a Product ID');
                return;
            }
            
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('product-details-container').classList.add('hidden');
            document.getElementById('error-message').classList.add('hidden');
            
            try {
                const response = await fetch(`${API_URL}/api/track/${productId}`);
                const data = await response.json();
                
                document.getElementById('loading').classList.add('hidden');
                
                if (data.success) {
                    displayProductDetails(data.product);
                } else {
                    showError(data.error || 'Product not found on blockchain');
                }
                
            } catch (error) {
                document.getElementById('loading').classList.add('hidden');
                showError('Connection error. Please try again.');
            }
        }

        function showError(message) {
            document.getElementById('error-text').textContent = message;
            document.getElementById('error-message').classList.remove('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function displayProductDetails(product) {
            document.getElementById('product-details-container').classList.remove('hidden');
            
            const productInfoHTML = `
                <div class="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-lg border-2 border-green-200">
                    <h4 class="text-3xl font-bold text-gray-800 mb-6">${product.productName}</h4>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-white p-4 rounded-lg shadow">
                            <p class="text-sm text-gray-600 mb-1">Product ID</p>
                            <p class="text-lg font-bold text-gray-800 font-mono">${product.productId}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <p class="text-sm text-gray-600 mb-1">Variety</p>
                            <p class="text-lg font-bold text-gray-800">${product.variety || 'Standard'}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <p class="text-sm text-gray-600 mb-1">Quantity</p>
                            <p class="text-lg font-bold text-gray-800">${product.quantity} kg</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <p class="text-sm text-gray-600 mb-1">Quality Grade</p>
                            <p class="text-lg font-bold text-green-600">${product.qualityGrade}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <p class="text-sm text-gray-600 mb-1">Farm Location</p>
                            <p class="text-lg font-bold text-gray-800">${product.farmLocation}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow">
                            <p class="text-sm text-gray-600 mb-1">Harvest Date</p>
                            <p class="text-lg font-bold text-gray-800">${product.harvestDate}</p>
                        </div>
                        <div class="bg-white p-4 rounded-lg shadow col-span-full">
                            <p class="text-sm text-gray-600 mb-1">Current Status</p>
                            <p class="text-lg font-bold text-blue-600">${product.currentStage}</p>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('product-info').innerHTML = productInfoHTML;
            
            let historyHTML = '<div class="space-y-6">';
            
            product.history.forEach((item, index) => {
                const isLast = index === product.history.length - 1;
                
                historyHTML += `
                    <div class="relative pl-8 pb-8">
                        ${!isLast ? '<div class="absolute left-4 top-8 bottom-0 w-0.5 bg-green-300"></div>' : ''}
                        
                        <div class="absolute left-0 top-0 w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-white font-bold">
                            ${index + 1}
                        </div>
                        
                        <div class="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-5 shadow-lg border-2 border-gray-200">
                            <div class="flex justify-between items-start mb-3">
                                <h5 class="text-xl font-bold text-gray-800">${item.stage}</h5>
                                <span class="text-sm text-gray-500 bg-white px-3 py-1 rounded-full">${item.timestamp}</span>
                            </div>
                            
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                                <div>
                                    <p class="text-gray-600">Handler:</p>
                                    <p class="font-semibold text-gray-800">${item.handlerName}</p>
                                </div>
                                <div>
                                    <p class="text-gray-600">Location:</p>
                                    <p class="font-semibold text-gray-800">${item.location || 'Not specified'}</p>
                                </div>
                                <div>
                                    <p class="text-gray-600">Temperature:</p>
                                    <p class="font-semibold text-gray-800">${item.temperature || 'N/A'}</p>
                                </div>
                                <div>
                                    <p class="text-gray-600">Humidity:</p>
                                    <p class="font-semibold text-gray-800">${item.humidity || 'N/A'}</p>
                                </div>
                            </div>
                            
                            ${item.notes ? `
                                <div class="mt-3 pt-3 border-t border-gray-300">
                                    <p class="text-sm text-gray-600">Notes:</p>
                                    <p class="text-sm text-gray-700 italic">${item.notes}</p>
                                </div>
                            ` : ''}

                            <div class="mt-4 pt-3 border-t border-gray-300">
                                <p class="text-xs text-gray-500 mb-1">Blockchain Transaction</p>
                                <p class="text-xs font-mono bg-gray-200 p-2 rounded break-all text-blue-700">${item.transactionHash}</p>
                            </div>

                        </div>
                    </div>
                `;
            });
            
            historyHTML += '</div>';
            
            document.getElementById('product-history').innerHTML = historyHTML;
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    </script>

</body>
</html>
'''

# Run both servers
def run_backend():
    backend_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_customer():
    customer_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("SERVERS STARTING...")
    print("=" * 60)
    print("Backend Management UI: http://localhost:5000")
    print("Customer Tracking UI:  http://localhost:5001")
    print(f"QR Codes Directory:    {os.path.abspath(QR_CODE_DIR)}")
    print("=" * 60)
    print("\nHow to use:")
    print("1. Open http://localhost:5000 to register/update products")
    print("2. Register a banana with ID like 'BANANA-001'")
    print("3. QR code will be automatically generated and saved")
    print("4. Download the QR code from the interface")
    print("5. Scan QR code or open http://localhost:5001 to track")
    print("=" * 60 + "\n")
    
    # Start both servers in separate threads
    import time
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    customer_thread = threading.Thread(target=run_customer, daemon=True)
    
    backend_thread.start()
    customer_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        print("Goodbye!")

