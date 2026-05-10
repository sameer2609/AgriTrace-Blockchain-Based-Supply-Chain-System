from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from web3 import Web3, EthereumTesterProvider
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# Connect to eth-tester blockchain (READ-ONLY)
print("Connecting to blockchain...")
w3 = Web3(EthereumTesterProvider())

# Load contract
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

if not CONTRACT_ADDRESS:
    print("ERROR: CONTRACT_ADDRESS not set in .env file")
    print("Please run deploy.py first!")
    exit()

# Load ABI
try:
    with open('contract_abi.json', 'r') as f:
        CONTRACT_ABI = json.load(f)
except FileNotFoundError:
    print("ERROR: contract_abi.json not found")
    print("Please run deploy.py first!")
    exit()

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

STAGES = ['Harvested', 'In Warehouse', 'In Transit', 'At Distributor', 'At Retailer', 'Sold']

# Serve customer UI
@app.route('/')
def index():
    return render_template_string(CUSTOMER_HTML)

# API endpoint for customers to track products
@app.route('/api/track/<product_id>', methods=['GET'])
def track_product(product_id):
    """Track product - Read-only endpoint for customers"""
    try:
        exists = contract.functions.productExistsCheck(product_id).call()
        if not exists:
            return jsonify({
                'success': False,
                'error': 'Product not found on blockchain'
            }), 404
        
        product = contract.functions.getProduct(product_id).call()
        history = contract.functions.getProductHistory(product_id).call()
        
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
                    'notes': h[7]
                }
                for h in history
            ]
        }
        
        return jsonify({'success': True, 'product': product_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        block_number = w3.eth.block_number
        return jsonify({
            'status': 'OK',
            'blockchain': 'Connected',
            'network': 'eth-tester',
            'chainId': w3.eth.chain_id,
            'blockNumber': block_number,
            'contractAddress': CONTRACT_ADDRESS
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'error': str(e)}), 500

# HTML template for customer UI
CUSTOMER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Track Your Product - Farm Trace</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-green-50 min-h-screen p-4">
    
    <div class="max-w-3xl mx-auto">
        <div class="bg-white rounded-lg shadow-xl p-8 mb-6 text-center">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">Farm Trace</h1>
            <p class="text-gray-600 text-lg">Track Your Product Journey</p>
            <p class="text-sm text-gray-500 mt-2">Enter Product ID to see complete farm-to-table journey</p>
        </div>

        <div class="bg-white rounded-lg shadow-xl p-8 mb-6">
            <div class="text-center mb-6">
                <h2 class="text-2xl font-bold text-gray-800 mb-2">Enter Product ID</h2>
                <p class="text-gray-600">Type the ID from your product packaging</p>
            </div>
            
            <div class="flex flex-col gap-4">
                <input 
                    type="text" 
                    id="searchId" 
                    placeholder="Example: FRUIT-ABC123XYZ" 
                    class="w-full px-6 py-4 text-center text-xl font-mono border-4 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 uppercase"
                    onkeypress="if(event.key === 'Enter') searchProduct()"
                >
                
                <button 
                    onclick="searchProduct()" 
                    class="w-full bg-blue-600 text-white py-4 rounded-lg text-xl font-bold hover:bg-blue-700 transition shadow-lg">
                    Track Product
                </button>
            </div>

            <div id="loading" class="hidden mt-6 text-center">
                <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600"></div>
                <p class="text-gray-600 mt-3 text-lg">Searching blockchain...</p>
            </div>
        </div>

        <div id="product-details-container" class="hidden">
            <div class="bg-white rounded-lg shadow-xl p-6 mb-6">
                <h3 class="text-2xl font-bold text-gray-800 mb-6 border-b-2 pb-3">Product Information</h3>
                <div id="product-info" class="space-y-4"></div>
            </div>

            <div class="bg-white rounded-lg shadow-xl p-6 mb-6">
                <h3 class="text-2xl font-bold text-gray-800 mb-6 border-b-2 pb-3">Supply Chain Journey</h3>
                <p class="text-gray-600 mb-6">Complete tracking from farm to your hands</p>
                <div id="product-history" class="relative"></div>
            </div>

            <div class="bg-gradient-to-r from-green-50 to-blue-50 border-4 border-green-500 rounded-lg p-6 text-center shadow-lg">
                <div class="text-6xl mb-3">✓</div>
                <h4 class="font-bold text-green-800 text-xl mb-2">Blockchain Verified</h4>
                <p class="text-sm text-green-700 mb-1">All information is stored on blockchain and cannot be tampered with.</p>
            </div>

            <div class="text-center mt-6">
                <button onclick="resetSearch()" class="bg-gray-600 text-white px-8 py-3 rounded-lg hover:bg-gray-700 font-semibold">
                    Track Another Product
                </button>
            </div>
        </div>

        <div id="error-message" class="hidden">
            <div class="bg-red-50 border-4 border-red-500 rounded-lg p-6 text-center shadow-xl">
                <div class="text-6xl mb-3">✗</div>
                <h4 class="font-bold text-red-800 text-xl mb-2">Product Not Found</h4>
                <p class="text-sm text-red-700 mb-4" id="error-text"></p>
                <button onclick="resetSearch()" class="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 font-semibold">
                    Try Again
                </button>
            </div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;

        function resetSearch() {
            document.getElementById('searchId').value = '';
            document.getElementById('product-details-container').classList.add('hidden');
            document.getElementById('error-message').classList.add('hidden');
            document.getElementById('loading').classList.add('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });
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
    port = 5001
    print('=' * 50)
    print('CUSTOMER TRACKING APP - Farm Trace')
    print('=' * 50)
    print(f'Customer UI running on: http://localhost:{port}')
    print(f'Contract: {CONTRACT_ADDRESS}')
    print('READ-ONLY MODE - eth-tester blockchain')
    print('=' * 50)
    app.run(host='0.0.0.0', port=port, debug=True)