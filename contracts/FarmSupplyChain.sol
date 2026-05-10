// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract FarmSupplyChain {
    enum Stage { Harvested, InWarehouse, InTransit, AtDistributor, AtRetailer, Sold }
    
    struct Product {
        string productId;
        string productName;
        string variety;
        uint256 quantity;
        string qualityGrade;
        address farmer;
        string farmLocation;
        uint256 harvestDate;
        Stage currentStage;
        bool exists;
    }
    
    struct StageUpdate {
        address handler;
        string handlerName;
        Stage stage;
        string location;
        string temperature;
        string humidity;
        uint256 timestamp;
        string notes;
    }
    
    mapping(string => Product) public products;
    mapping(string => StageUpdate[]) public productHistory;
    string[] public productIds;
    
    event ProductRegistered(string indexed productId, address indexed farmer, uint256 timestamp);
    event ProductUpdated(string indexed productId, Stage stage, address indexed handler, uint256 timestamp);
    
    function registerProduct(
        string memory _productId,
        string memory _productName,
        string memory _variety,
        uint256 _quantity,
        string memory _qualityGrade,
        string memory _farmLocation,
        string memory _temperature,
        string memory _humidity,
        string memory _farmerName,
        string memory _notes
    ) public {
        require(!products[_productId].exists, "Product already exists");
        
        products[_productId] = Product({
            productId: _productId,
            productName: _productName,
            variety: _variety,
            quantity: _quantity,
            qualityGrade: _qualityGrade,
            farmer: msg.sender,
            farmLocation: _farmLocation,
            harvestDate: block.timestamp,
            currentStage: Stage.Harvested,
            exists: true
        });
        
        productIds.push(_productId);
        
        productHistory[_productId].push(StageUpdate({
            handler: msg.sender,
            handlerName: _farmerName,
            stage: Stage.Harvested,
            location: _farmLocation,
            temperature: _temperature,
            humidity: _humidity,
            timestamp: block.timestamp,
            notes: _notes
        }));
        
        emit ProductRegistered(_productId, msg.sender, block.timestamp);
    }
    
    function updateProduct(
        string memory _productId,
        Stage _stage,
        string memory _location,
        string memory _temperature,
        string memory _humidity,
        string memory _handlerName,
        string memory _notes
    ) public {
        require(products[_productId].exists, "Product does not exist");
        
        products[_productId].currentStage = _stage;
        
        productHistory[_productId].push(StageUpdate({
            handler: msg.sender,
            handlerName: _handlerName,
            stage: _stage,
            location: _location,
            temperature: _temperature,
            humidity: _humidity,
            timestamp: block.timestamp,
            notes: _notes
        }));
        
        emit ProductUpdated(_productId, _stage, msg.sender, block.timestamp);
    }
    
    function getProduct(string memory _productId) public view returns (
        string memory productName,
        string memory variety,
        uint256 quantity,
        string memory qualityGrade,
        address farmer,
        string memory farmLocation,
        uint256 harvestDate,
        Stage currentStage
    ) {
        Product memory p = products[_productId];
        return (
            p.productName,
            p.variety,
            p.quantity,
            p.qualityGrade,
            p.farmer,
            p.farmLocation,
            p.harvestDate,
            p.currentStage
        );
    }
    
    function getProductHistory(string memory _productId) public view returns (StageUpdate[] memory) {
        return productHistory[_productId];
    }
    
    function productExistsCheck(string memory _productId) public view returns (bool) {
        return products[_productId].exists;
    }
}
