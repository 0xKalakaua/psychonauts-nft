// SPDX-License-Identifier: MIT

/**
FTMdead Presents
██████╗░░██████╗██╗░░░██╗░█████╗░██╗░░██╗░█████╗░███╗░░██╗░█████╗░██╗░░░██╗████████╗░██████╗
██╔══██╗██╔════╝╚██╗░██╔╝██╔══██╗██║░░██║██╔══██╗████╗░██║██╔══██╗██║░░░██║╚══██╔══╝██╔════╝
██████╔╝╚█████╗░░╚████╔╝░██║░░╚═╝███████║██║░░██║██╔██╗██║███████║██║░░░██║░░░██║░░░╚█████╗░
██╔═══╝░░╚═══██╗░░╚██╔╝░░██║░░██╗██╔══██║██║░░██║██║╚████║██╔══██║██║░░░██║░░░██║░░░░╚═══██╗
██║░░░░░██████╔╝░░░██║░░░╚█████╔╝██║░░██║╚█████╔╝██║░╚███║██║░░██║╚██████╔╝░░░██║░░░██████╔╝
╚═╝░░░░░╚═════╝░░░░╚═╝░░░░╚════╝░╚═╝░░╚═╝░╚════╝░╚═╝░░╚══╝╚═╝░░╚═╝░╚═════╝░░░░╚═╝░░░╚═════╝░
A Gimpies Project                                                     contract by 0xKalakaua
*/

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";

contract Psychonauts is AccessControlEnumerable, ERC721Enumerable, ERC721URIStorage {
    using Counters for Counters.Counter;
    using Strings for uint;

    Counters.Counter public tokenIdTracker;
    uint public max_supply;
    uint public price;

    mapping(uint => bool) private hasPyschonaut;
    string private _baseTokenURI;
    string private _baseExtension;
    string private _notRevealedURI;
    bool private _revealed = false;
    bool private _openMint = false;
    bool private _openPublicMint = false;
    IERC721 private _theGimpies;
    address payable private _wallet;

    constructor (
        string memory name,
        string memory symbol, 
        string memory baseURI,
        string memory baseExtension,
        string memory notRevealedURI,
        uint mintPrice,
        uint max,
        address theGimpiesAddress,
        address payable wallet
    )
        ERC721 (name, symbol)
    {
        tokenIdTracker.increment(); // Start collection at 1
        max_supply = max;
        price = mintPrice;
        _baseTokenURI = baseURI;
        _baseExtension = baseExtension;
        _notRevealedURI = notRevealedURI;
        _theGimpies = IERC721(theGimpiesAddress);
        _wallet = wallet;
        _setupRole(DEFAULT_ADMIN_ROLE, wallet);
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }

    modifier onlyAdmin() {
        require(hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Psychonauts: caller is not admin");
        _;
    }

    function revealPsychonauts() external onlyAdmin {
        _revealed = true;
    }

    function setBaseURI(string memory baseURI) external onlyAdmin {
        _baseTokenURI = baseURI;
    }

    function setBaseExtension(string memory baseExtension) external onlyAdmin {
        _baseExtension = baseExtension;
    }

    function setTokenURI(uint tokenId, string memory _tokenURI) external onlyAdmin {
        _setTokenURI(tokenId, _tokenURI);
    }

    function setPrice(uint mintPrice) external onlyAdmin {
        price = mintPrice;
    }

    function mintSwitch() external onlyAdmin {
        _openMint = !_openMint;
    }

    function publicMintSwitch() external onlyAdmin {
        _openPublicMint = !_openPublicMint;
    }

    function OGmint(uint[] calldata gimpiesTokenIds) public payable {
        uint numPsychonauts = gimpiesTokenIds.length;

        require(_openMint == true, "Psychonauts: minting is currently not open");
        require(tokenIdTracker.current() <= max_supply, "Psychonauts: all tokens have been minted");
        require(
            tokenIdTracker.current() + numPsychonauts <= max_supply + 1,
            "Psychonauts: tried to mint too many"
        );
        require(msg.value == price * numPsychonauts, "Psychonauts: amount sent is incorrect");

        for (uint i=0; i < numPsychonauts; ++i) {
            uint tokenId = tokenIdTracker.current();
            uint gimpTokenId = gimpiesTokenIds[i];

            require(
                _theGimpies.ownerOf(gimpTokenId) == msg.sender,
                "Psychonauts: caller is not owner of that Gimp"
            );
            require(
                hasPyschonaut[gimpTokenId] == false,
                "Psychonauts: this Gimp has already minted a Psychonaut"
            );
            tokenIdTracker.increment();
            _safeMint(msg.sender, tokenId);
            _setTokenURI(
                tokenId, string(abi.encodePacked(tokenId.toString(), _baseExtension))
            );
            hasPyschonaut[gimpTokenId] = true;
        }

        _wallet.transfer(msg.value);
    }

    function publicMint() public payable {
        uint tokenId = tokenIdTracker.current();

        require(_openMint == true, "Psychonauts: minting is currently not open");
        require(_openPublicMint == true, "Psychonauts: public minting is currently not open");
        require(tokenIdTracker.current() <= max_supply, "Psychonauts: all tokens have been minted");
        require(msg.value == price, "Psychonauts: amount sent is incorrect");

        tokenIdTracker.increment();
        _safeMint(msg.sender, tokenId);
        _setTokenURI(
            tokenId, string(abi.encodePacked(tokenId.toString(), _baseExtension))
        );

        _wallet.transfer(msg.value);
    }

    function hasGimpMintedPsychonaut(uint gimpiesTokenId) public view returns (bool) {
        return hasPyschonaut[gimpiesTokenId];
    }

    function tokenURI(uint tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        if (!_revealed) {
            require(_exists(tokenId), "Psychonauts: URI query for nonexistent token");
            return _notRevealedURI;
        }
        return ERC721URIStorage.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual override(AccessControlEnumerable, ERC721, ERC721Enumerable)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function _baseURI() internal view virtual override returns (string memory) {
        return _baseTokenURI;
    }

    function _burn(uint tokenId) internal virtual override(ERC721, ERC721URIStorage) {
        return ERC721URIStorage._burn(tokenId);
    }

    function _beforeTokenTransfer(address from, address to, uint tokenId)
        internal
        virtual override(ERC721, ERC721Enumerable)
    {
        super._beforeTokenTransfer(from, to, tokenId);
    }
}
