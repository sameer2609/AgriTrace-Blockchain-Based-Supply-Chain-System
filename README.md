# Farm Trace Blockchain: Enhancing Transparency and Traceability in Agricultural Supply Chain Management

## 📌 Description

This project implements a blockchain-based system to improve transparency and traceability in agricultural supply chains. Each product is tracked from farm to consumer using smart contracts, ensuring data integrity and trust.

---

## 🚀 Features

* Smart contract-based product tracking
* End-to-end supply chain visibility
* QR code generation for product verification
* Customer interface for real-time tracking
* Secure and tamper-proof data storage

---

## 🛠 Technologies Used

* **Blockchain:** Solidity
* **Backend:** Python (Flask)
* **Blockchain Interaction:** Web3.py
* **Frontend:** HTML, Tailwind CSS
* **QR Code:** qrcode library
* **Local Blockchain:** Ethereum Tester

---

## 🧩 System Architecture

1. User registers product via web interface
2. Flask backend sends data to smart contract
3. Smart contract stores product details on blockchain
4. QR code is generated with product ID
5. Customer scans QR → fetches product data from blockchain

---

## 📂 Project Structure

contracts/           → Smart contracts
app.py               → Main backend application
customer_app.py      → Customer interface
deploy.py            → Smart contract deployment
contract_abi.json    → Contract ABI
compiled_contract.json → Compiled contract
qr_codes/            → Generated QR codes

---

## ⚙️ Requirements

Install dependencies using:

pip install -r requirements.txt

---

## ▶️ How to Run

1. Deploy the smart contract:
   python deploy.py

2. Run backend:
   python app.py

3. Run customer interface:
   python customer_app.py

---

## 🔍 How It Works

* Each product gets a unique ID
* Data is stored on blockchain
* QR code links to product tracking
* Customer scans QR → retrieves full history

---

## ⚠️ Note

* `.env` file is excluded for security reasons
* Uses local blockchain (Ethereum Tester) for demonstration

---

## 📌 Future Improvements

* Integration with real blockchain (Ethereum / Polygon)
* Database integration for user management
* Role-based access control
* Mobile app for QR scanning

---

## 👨‍💻 Authors

Adapa Greeshmi Karunya,
Athuluri Meghana,
Uggirala Sairam Manikanta,
Duggirala Sameer,
Bharath Singh Jebaraj,
Vivekrabinson K.
