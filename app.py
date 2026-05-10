
from flask import Flask, request, jsonify, render_template_string, send_file, session, redirect, url_for
from flask_cors import CORS
from web3 import Web3, EthereumTesterProvider
from solcx import compile_standard, install_solc
from datetime import datetime
import json
import threading
import qrcode
import os
from io import BytesIO
import hashlib

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

# Indian states and cities data
INDIA_STATES_CITIES = {
    'Andhra Pradesh': ['Visakhapatnam', 'Vijayawada', 'Guntur', 'Nellore', 'Kurnool', 'Tirupati', 'Rajahmundry', 'Kakinada', 'Anantapur', 'Eluru'],
    'Arunachal Pradesh': ['Itanagar', 'Tawang', 'Ziro', 'Pasighat', 'Bomdila', 'Tezu', 'Khonsa', 'Anini', 'Yingkiong', 'Changlang'],
    'Assam': ['Guwahati', 'Silchar', 'Dibrugarh', 'Jorhat', 'Nagaon', 'Tinsukia', 'Tezpur', 'Bongaigaon', 'Karimganj', 'Sivasagar'],
    'Bihar': ['Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur', 'Purnia', 'Darbhanga', 'Bihar Sharif', 'Arrah', 'Begusarai', 'Katihar'],
    'Chhattisgarh': ['Raipur', 'Bhilai', 'Bilaspur', 'Durg', 'Korba', 'Raigarh', 'Ambikapur', 'Dhamtari', 'Janjgir', 'Mahasamund'],
    'Goa': ['Panaji', 'Margao', 'Vasco da Gama', 'Mapusa', 'Ponda', 'Bicholim', 'Curchorem', 'Sanquelim', 'Cortalim', 'Quepem'],
    'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar', 'Bhavnagar', 'Jamnagar', 'Junagadh', 'Anand', 'Nadiad'],
    'Haryana': ['Gurugram', 'Faridabad', 'Panipat', 'Ambala', 'Karnal', 'Sonipat', 'Rohtak', 'Hisar', 'Bhiwani', 'Yamunanagar'],
    'Himachal Pradesh': ['Shimla', 'Manali', 'Dharamshala', 'Solan', 'Mandi', 'Kullu', 'Palampur', 'Bilaspur', 'Chamba', 'Hamirpur'],
    'Jharkhand': ['Ranchi', 'Jamshedpur', 'Dhanbad', 'Bokaro', 'Deoghar', 'Phusro', 'Hazaribagh', 'Giridih', 'Ramgarh', 'Medininagar'],
    'Karnataka': ['Bengaluru', 'Mysuru', 'Hubballi', 'Mangaluru', 'Belagavi', 'Gulbarga', 'Davanagere', 'Ballari', 'Shivamogga', 'Tumakuru'],
    'Kerala': ['Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Thrissur', 'Kollam', 'Palakkad', 'Alappuzha', 'Malappuram', 'Kannur', 'Kasaragod'],
    'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur', 'Ujjain', 'Sagar', 'Ratlam', 'Satna', 'Rewa', 'Murwara'],
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik', 'Aurangabad', 'Solapur', 'Amravati', 'Navi Mumbai', 'Kolhapur'],
    'Manipur': ['Imphal', 'Thoubal', 'Bishnupur', 'Churachandpur', 'Kakching', 'Ukhrul', 'Senapati', 'Tamenglong', 'Chandel', 'Noney'],
    'Meghalaya': ['Shillong', 'Tura', 'Nongstoin', 'Jowai', 'Baghmara', 'Williamnagar', 'Resubelpara', 'Mawsynram', 'Khliehriat', 'Nongpoh'],
    'Mizoram': ['Aizawl', 'Lunglei', 'Champhai', 'Serchhip', 'Kolasib', 'Lawngtlai', 'Saitual', 'Saitual', 'Hnahthial', 'Mamit'],
    'Nagaland': ['Kohima', 'Dimapur', 'Mokokchung', 'Tuensang', 'Wokha', 'Zunheboto', 'Phek', 'Kiphire', 'Longleng', 'Peren'],
    'Odisha': ['Bhubaneswar', 'Cuttack', 'Rourkela', 'Brahmapur', 'Sambalpur', 'Puri', 'Balasore', 'Angul', 'Bhadrak', 'Baripada'],
    'Punjab': ['Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda', 'Mohali', 'Firozpur', 'Pathankot', 'Hoshiarpur', 'Kapurthala'],
    'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota', 'Ajmer', 'Bikaner', 'Bhilwara', 'Alwar', 'Bharatpur', 'Sikar'],
    'Sikkim': ['Gangtok', 'Namchi', 'Gyalshing', 'Mangan', 'Rangpo', 'Jorethang', 'Singtam', 'Ravangla', 'Pelling', 'Lachung'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem', 'Tirunelveli', 'Erode', 'Vellore', 'Thoothukudi', 'Thanjavur'],
    'Telangana': ['Hyderabad', 'Warangal', 'Nizamabad', 'Karimnagar', 'Khammam', 'Ramagundam', 'Mahabubnagar', 'Nalgonda', 'Adilabad', 'Miryalaguda'],
    'Tripura': ['Agartala', 'Udaipur', 'Dharmanagar', 'Pratapgarh', 'Kailashahar', 'Belonia', 'Khowai', 'Amarpur', 'Teliamura', 'Kamalpur'],
    'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Ghaziabad', 'Agra', 'Varanasi', 'Meerut', 'Allahabad', 'Bareilly', 'Aligarh', 'Moradabad'],
    'Uttarakhand': ['Dehradun', 'Haridwar', 'Roorkee', 'Haldwani', 'Rishikesh', 'Kashipur', 'Rudrapur', 'Kashipur', 'Pithoragarh', 'Mukteshwar'],
    'West Bengal': ['Kolkata', 'Howrah', 'Durgapur', 'Siliguri', 'Asansol', 'Bardhaman', 'Malda', 'Kharagpur', 'Berhampore', 'Baharampur'],
    'Delhi': ['New Delhi', 'North Delhi', 'South Delhi', 'East Delhi', 'West Delhi', 'Central Delhi', 'North East Delhi', 'North West Delhi', 'South West Delhi', 'South East Delhi'],
    'Jammu & Kashmir': ['Srinagar', 'Jammu', 'Anantnag', 'Baramulla', 'Sopore', 'Kulgam', 'Pulwama', 'Shopian', 'Bandipora', 'Ganderbal'],
    'Ladakh': ['Leh', 'Kargil', 'Nubra', 'Zanskar', 'Changthang', 'Sham Valley', 'Khardung La', 'Pangong Tso', 'Tso Moriri', 'Hemis'],
    'Lakshadweep': ['Kavaratti', 'Agatti', 'Amini', 'Andrott', 'Bitra', 'Chetlat', 'Kadmat', 'Kalpeni', 'Kiltan', 'Minicoy'],
    'Puducherry': ['Puducherry', 'Karaikal', 'Mahe', 'Yanam', 'Oulgaret', 'Villianur', 'Mudaliarpet', 'Lawspet', 'Ariyankuppam', 'Bahour'],
    'Andaman & Nicobar': ['Port Blair', 'Car Nicobar', 'Havelock Island', 'Neil Island', 'Mayabunder', 'Diglipur', 'Rangat', 'Long Island', 'Little Andaman', 'Great Nicobar']
}

# Food categories and common items
FOOD_CATEGORIES = {
    'Fruits': ['Apple', 'Banana', 'Orange', 'Mango', 'Grapes', 'Strawberry', 'Pineapple', 'Watermelon', 'Papaya', 'Guava'],
    'Vegetables': ['Tomato', 'Potato', 'Onion', 'Carrot', 'Cabbage', 'Spinach', 'Broccoli', 'Cauliflower', 'Capsicum', 'Cucumber'],
    'Grains': ['Rice', 'Wheat', 'Corn', 'Barley', 'Oats', 'Millet', 'Quinoa', 'Sorghum'],
    'Dairy': ['Milk', 'Cheese', 'Butter', 'Yogurt', 'Curd', 'Ghee', 'Cream', 'Paneer'],
    'Pulses': ['Lentil', 'Chickpea', 'Beans', 'Peas', 'Soybean', 'Moong', 'Masoor', 'Urad'],
    'Spices': ['Turmeric', 'Chili', 'Coriander', 'Cumin', 'Pepper', 'Cardamom', 'Cinnamon', 'Clove'],
    'Other': ['Honey', 'Jaggery', 'Sugar', 'Salt', 'Oil', 'Tea', 'Coffee', 'Nuts']
}

# Flatten all items for easy access
ALL_FOOD_ITEMS = []
for category, items in FOOD_CATEGORIES.items():
    ALL_FOOD_ITEMS.extend(items)

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

# ============== UNIFIED APP WITH AUTHENTICATION ==============
app = Flask(__name__)
app.secret_key = 'farm_trace_secret_key_2024'  # Change in production
CORS(app)

# Simple user storage (in production, use a proper database)
USERS = {
    'admin': {'password': hashlib.sha256('admin123'.encode()).hexdigest(), 'role': 'staff'},
    'staff1': {'password': hashlib.sha256('staff123'.encode()).hexdigest(), 'role': 'staff'},
    'customer': {'password': hashlib.sha256('customer123'.encode()).hexdigest(), 'role': 'customer'}
}

# ============== AUTHENTICATION ROUTES ==============
@app.route('/')
def index():
    if 'user' in session:
        user_role = session.get('role')
        if user_role == 'staff':
            return render_template_string(STAFF_HTML)
        else:
            return render_template_string(CUSTOMER_HTML)
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', '')
    password = request.json.get('password', '')
    
    if username in USERS and USERS[username]['password'] == hashlib.sha256(password.encode()).hexdigest():
        session['user'] = username
        session['role'] = USERS[username]['role']
        return jsonify({'success': True, 'role': USERS[username]['role']})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username', '')
    password = request.json.get('password', '')
    role = request.json.get('role', 'customer')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    if username in USERS:
        return jsonify({'success': False, 'error': 'Username already exists'}), 400
    
    USERS[username] = {
        'password': hashlib.sha256(password.encode()).hexdigest(),
        'role': role
    }
    
    return jsonify({'success': True, 'message': 'Registration successful'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/staff')
def staff_dashboard():
    if 'user' not in session or session.get('role') != 'staff':
        return redirect(url_for('index'))
    return render_template_string(STAFF_HTML)

@app.route('/customer')
def customer_dashboard():
    if 'user' not in session or session.get('role') != 'customer':
        return redirect(url_for('index'))
    return render_template_string(CUSTOMER_HTML)

@app.route('/api/products/register', methods=['POST'])
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

@app.route('/api/qrcode/<product_id>', methods=['GET'])
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

@app.route('/api/products/update', methods=['POST'])
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

@app.route('/api/products/<product_id>', methods=['GET'])
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

@app.route('/api/health', methods=['GET'])
def health_backend():
    return jsonify({
        'status': 'OK',
        'contract': contract_address,
        'blockNumber': w3.eth.block_number,
        'account': account
    })

# ============== CUSTOMER APP ROUTES ==============
@app.route('/api/track/<product_id>', methods=['GET'])
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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'contract': contract_address,
        'blockNumber': w3.eth.block_number,
        'account': account
    })

# ============== HTML TEMPLATES ==============
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Farm Supply Chain - Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-green-50 to-blue-50 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full">
        <div class="bg-white rounded-2xl shadow-2xl p-8">
            <div class="text-center mb-8">
                <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-green-600 to-blue-600 rounded-full mb-4">
                    <i class="fas fa-leaf text-white text-3xl"></i>
                </div>
                <h1 class="text-3xl font-bold text-gray-800 mb-2">Farm Supply Chain</h1>
                <p class="text-gray-600">Login to your account</p>
            </div>

            <div id="loginForm">
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Username</label>
                        <input type="text" id="username" 
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Enter your username">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                        <input type="password" id="password" 
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Enter your password">
                    </div>
                    
                    <button onclick="handleLogin()" 
                        class="w-full bg-gradient-to-r from-green-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all transform hover:scale-105 shadow-lg">
                        <i class="fas fa-sign-in-alt mr-2"></i>Login
                    </button>
                </div>

                <div class="mt-6 text-center">
                    <p class="text-gray-600">Don't have an account? 
                        <button onclick="showRegister()" class="text-green-600 hover:text-green-700 font-semibold">Register here</button>
                    </p>
                </div>

                <div class="mt-4 p-4 bg-gray-50 rounded-lg">
                    <p class="text-xs text-gray-500 font-semibold mb-2">Demo Accounts:</p>
                    <p class="text-xs text-gray-600">Staff: admin / admin123</p>
                    <p class="text-xs text-gray-600">Customer: customer / customer123</p>
                </div>
            </div>

            <div id="registerForm" class="hidden">
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Username</label>
                        <input type="text" id="regUsername" 
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Choose a username">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                        <input type="password" id="regPassword" 
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Choose a password">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Account Type</label>
                        <select id="regRole" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            <option value="customer">Customer (Track Products)</option>
                            <option value="staff">Staff (Manage Products)</option>
                        </select>
                    </div>
                    
                    <button onclick="handleRegister()" 
                        class="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 shadow-lg">
                        <i class="fas fa-user-plus mr-2"></i>Register
                    </button>
                </div>

                <div class="mt-6 text-center">
                    <p class="text-gray-600">Already have an account? 
                        <button onclick="showLogin()" class="text-green-600 hover:text-green-700 font-semibold">Login here</button>
                    </p>
                </div>
            </div>

            <div id="message" class="mt-4 hidden"></div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;

        function showRegister() {
            document.getElementById('loginForm').classList.add('hidden');
            document.getElementById('registerForm').classList.remove('hidden');
            document.getElementById('message').classList.add('hidden');
        }

        function showLogin() {
            document.getElementById('registerForm').classList.add('hidden');
            document.getElementById('loginForm').classList.remove('hidden');
            document.getElementById('message').classList.add('hidden');
        }

        function showMessage(message, isError = false) {
            const messageDiv = document.getElementById('message');
            messageDiv.className = `mt-4 p-4 rounded-lg ${isError ? 'bg-red-50 border-2 border-red-500 text-red-800' : 'bg-green-50 border-2 border-green-500 text-green-800'}`;
            messageDiv.innerHTML = `
                <div class="flex items-center gap-2">
                    <i class="fas ${isError ? 'fa-exclamation-circle' : 'fa-check-circle'}"></i>
                    <span>${message}</span>
                </div>
            `;
            messageDiv.classList.remove('hidden');
        }

        async function handleLogin() {
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;

            if (!username || !password) {
                showMessage('Please enter both username and password', true);
                return;
            }

            try {
                const response = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('Login successful! Redirecting...', false);
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showMessage(data.error || 'Login failed', true);
                }
            } catch (error) {
                showMessage('Connection error. Please try again.', true);
            }
        }

        async function handleRegister() {
            const username = document.getElementById('regUsername').value.trim();
            const password = document.getElementById('regPassword').value;
            const role = document.getElementById('regRole').value;

            if (!username || !password) {
                showMessage('Please enter both username and password', true);
                return;
            }

            try {
                const response = await fetch(`${API_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, role })
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('Registration successful! Please login.', false);
                    setTimeout(() => {
                        showLogin();
                        document.getElementById('username').value = username;
                    }, 1500);
                } else {
                    showMessage(data.error || 'Registration failed', true);
                }
            } catch (error) {
                showMessage('Connection error. Please try again.', true);
            }
        }

        // Allow Enter key to submit
        document.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                if (!document.getElementById('registerForm').classList.contains('hidden')) {
                    handleRegister();
                } else {
                    handleLogin();
                }
            }
        });
    </script>
</body>
</html>
'''

STAFF_HTML = '''
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
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-4xl font-bold flex items-center gap-3">
                        <i class="fas fa-tractor"></i>
                        Farm Supply Chain Management
                    </h1>
                    <p class="mt-2 text-green-100">Complete product lifecycle tracking on blockchain</p>
                </div>
                <div class="flex gap-2">
                    <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                        <i class="fas fa-user mr-1"></i>{{ session.get('user', 'Staff') }}
                    </span>
                    <a href="/logout" class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all text-sm">
                        <i class="fas fa-sign-out-alt mr-1"></i>Logout
                    </a>
                </div>
            </div>
        </header>

        <div class="flex gap-6">
            <!-- Sidebar Navigation -->
            <div class="w-64 bg-white rounded-lg shadow-lg p-4">
                <h3 class="text-lg font-bold text-gray-800 mb-4">Management Options</h3>
                <div class="space-y-2">
                    <button onclick="showSection('register')" id="registerBtn"
                        class="w-full text-left px-4 py-3 rounded-lg bg-green-600 text-white font-semibold hover:bg-green-700 transition-all">
                        <i class="fas fa-plus-circle mr-2"></i>Register New Product
                    </button>
                    <button onclick="showSection('update')" id="updateBtn"
                        class="w-full text-left px-4 py-3 rounded-lg bg-gray-200 text-gray-700 font-semibold hover:bg-gray-300 transition-all">
                        <i class="fas fa-edit mr-2"></i>Update Product Stage
                    </button>
                    <button onclick="showSection('search')" id="searchBtn"
                        class="w-full text-left px-4 py-3 rounded-lg bg-gray-200 text-gray-700 font-semibold hover:bg-gray-300 transition-all">
                        <i class="fas fa-search mr-2"></i>Search Product
                    </button>
                </div>
            </div>

            <!-- Main Content Area -->
            <div class="flex-1">
                <!-- Register Product Section -->
                <div id="registerSection" class="bg-white rounded-lg shadow-lg p-6">
                    <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                        <i class="fas fa-plus-circle text-green-600"></i>
                        Register New Product
                    </h2>
                    
                    <form id="registerForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Product ID *</label>
                        <input type="text" id="productId" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="e.g., APPLE-001, TOMATO-001, RICE-001">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Product Category *</label>
                        <select id="category" required onchange="updateProductOptions()"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            <option value="">-- Select Category --</option>
                            ''' + ''.join([f'<option value="{category}">{category}</option>' for category in FOOD_CATEGORIES.keys()]) + '''
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Product Name *</label>
                        <select id="productName" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            <option value="">-- Select Product --</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Custom Product (Optional)</label>
                        <input type="text" id="customProduct" 
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="Enter custom product name if not in list">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Variety/Type (Optional)</label>
                        <input type="text" id="variety" 
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            placeholder="e.g., Organic, Premium, Local">
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
                        <label class="block text-sm font-semibold text-gray-700 mb-2">State *</label>
                        <select id="state" required onchange="updateCityOptions()"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            <option value="">-- Select State --</option>
                            ''' + ''.join([f'<option value="{state}">{state}</option>' for state in INDIA_STATES_CITIES.keys()]) + '''
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">City *</label>
                        <select id="city" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            <option value="">-- Select City --</option>
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
                </form>
                </div>

                <!-- Update Product Section -->
                <div id="updateSection" class="bg-white rounded-lg shadow-lg p-6 hidden">
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
                        <label class="block text-sm font-semibold text-gray-700 mb-2">State</label>
                        <select id="updateState" onchange="updateCityOptionsForUpdate()"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="">-- Select State --</option>
                            ''' + ''.join([f'<option value="{state}">{state}</option>' for state in INDIA_STATES_CITIES.keys()]) + '''
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">City</label>
                        <select id="updateCity"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="">-- Select City --</option>
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
                </form>
                </div>

                <!-- Search Product Section -->
                <div id="searchSection" class="bg-white rounded-lg shadow-lg p-6 hidden">
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
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        
        // Food categories data
        const FOOD_CATEGORIES = ''' + json.dumps(FOOD_CATEGORIES) + ''';
        
        // States and cities data
        const INDIA_STATES_CITIES = ''' + json.dumps(INDIA_STATES_CITIES) + ''';

        // Update city options based on selected state (for registration form)
        function updateCityOptions() {
            const state = document.getElementById('state').value;
            const citySelect = document.getElementById('city');
            
            citySelect.innerHTML = '<option value="">-- Select City --</option>';
            
            if (state && INDIA_STATES_CITIES[state]) {
                INDIA_STATES_CITIES[state].forEach(city => {
                    citySelect.innerHTML += `<option value="${city}">${city}</option>`;
                });
            }
        }

        // Update city options based on selected state (for update form)
        function updateCityOptionsForUpdate() {
            const state = document.getElementById('updateState').value;
            const citySelect = document.getElementById('updateCity');
            
            citySelect.innerHTML = '<option value="">-- Select City --</option>';
            
            if (state && INDIA_STATES_CITIES[state]) {
                INDIA_STATES_CITIES[state].forEach(city => {
                    citySelect.innerHTML += `<option value="${city}">${city}</option>`;
                });
            }
        }

        // Update product options based on category
        function updateProductOptions() {
            const category = document.getElementById('category').value;
            const productSelect = document.getElementById('productName');
            
            productSelect.innerHTML = '<option value="">-- Select Product --</option>';
            
            if (category && FOOD_CATEGORIES[category]) {
                FOOD_CATEGORIES[category].forEach(item => {
                    productSelect.innerHTML += `<option value="${item}">${item}</option>`;
                });
            }
        }

        // Section switching function
        function showSection(section) {
            // Hide all sections
            document.getElementById('registerSection').classList.add('hidden');
            document.getElementById('updateSection').classList.add('hidden');
            document.getElementById('searchSection').classList.add('hidden');
            
            // Reset all button styles
            document.getElementById('registerBtn').className = 'w-full text-left px-4 py-3 rounded-lg bg-gray-200 text-gray-700 font-semibold hover:bg-gray-300 transition-all';
            document.getElementById('updateBtn').className = 'w-full text-left px-4 py-3 rounded-lg bg-gray-200 text-gray-700 font-semibold hover:bg-gray-300 transition-all';
            document.getElementById('searchBtn').className = 'w-full text-left px-4 py-3 rounded-lg bg-gray-200 text-gray-700 font-semibold hover:bg-gray-300 transition-all';
            
            // Show selected section and highlight button
            if (section === 'register') {
                document.getElementById('registerSection').classList.remove('hidden');
                document.getElementById('registerBtn').className = 'w-full text-left px-4 py-3 rounded-lg bg-green-600 text-white font-semibold hover:bg-green-700 transition-all';
            } else if (section === 'update') {
                document.getElementById('updateSection').classList.remove('hidden');
                document.getElementById('updateBtn').className = 'w-full text-left px-4 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-all';
            } else if (section === 'search') {
                document.getElementById('searchSection').classList.remove('hidden');
                document.getElementById('searchBtn').className = 'w-full text-left px-4 py-3 rounded-lg bg-purple-600 text-white font-semibold hover:bg-purple-700 transition-all';
            }
        }

        // Handle custom product input
        document.addEventListener('DOMContentLoaded', function() {
            const customProductInput = document.getElementById('customProduct');
            const productNameSelect = document.getElementById('productName');
            
            if (customProductInput && productNameSelect) {
                customProductInput.addEventListener('input', function() {
                    if (this.value.trim()) {
                        productNameSelect.value = '';
                        productNameSelect.required = false;
                    } else {
                        productNameSelect.required = true;
                    }
                });

                productNameSelect.addEventListener('change', function() {
                    if (this.value) {
                        customProductInput.value = '';
                    }
                });
            }
        });

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
                        productName: document.getElementById('customProduct').value.trim() || document.getElementById('productName').value,
                        variety: document.getElementById('variety').value,
                        quantity: document.getElementById('quantity').value,
                        qualityGrade: document.getElementById('qualityGrade').value,
                        farmLocation: document.getElementById('state').value + ', ' + document.getElementById('city').value,
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
                        location: document.getElementById('updateState').value + ', ' + document.getElementById('updateCity').value,
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
            <div class="flex justify-between items-center">
                <div class="flex-1">
                    <h1 class="text-3xl md:text-5xl font-bold mb-3 flex items-center justify-center gap-3">
                        <i class="fas fa-leaf"></i>
                        Farm Supply Chain Tracker
                    </h1>
                    <p class="text-base md:text-xl text-green-100">Verify your product's journey from farm to table</p>
                </div>
                <div class="flex gap-2">
                    <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                        <i class="fas fa-user mr-1"></i>{{ session.get('user', 'Customer') }}
                    </span>
                    <a href="/logout" class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all text-sm">
                        <i class="fas fa-sign-out-alt mr-1"></i>Logout
                    </a>
                </div>
            </div>
        </header>

        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-8">
            <h3 class="text-xl font-bold text-gray-800 mb-4 text-center">Enter Product ID or Scan QR Code</h3>
            
            <div class="flex flex-col md:flex-row gap-4 items-center mb-6">
                <input type="text" id="searchId" 
                    class="flex-1 px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:ring-4 focus:ring-green-500 focus:border-green-500 transition-all"
                    placeholder="Enter Product ID (e.g., APPLE-001, TOMATO-001)">
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

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("FARM SUPPLY CHAIN - UNIFIED SYSTEM")
    print("=" * 60)
    print("Server running on: http://localhost:5000")
    print(f"QR Codes Directory: {os.path.abspath(QR_CODE_DIR)}")
    print("=" * 60)
    print("\nHow to use:")
    print("1. Open http://localhost:5000")
    print("2. Login or register an account")
    print("3. Staff accounts can register/update products")
    print("4. Customer accounts can track products")
    print("\nDemo Accounts:")
    print("- Staff: admin / admin123")
    print("- Customer: customer / customer123")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

