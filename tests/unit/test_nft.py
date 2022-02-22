import pytest
import brownie
from brownie import network, accounts, Psychonauts, MockERC721

@pytest.fixture
def gimpies():
    dev = accounts[0]
    max_supply = 10
    gimpies = MockERC721.deploy("Gimpies Test", "GMP", max_supply, dev, {'from': dev})
    for i in range(max_supply):
        tx = gimpies.mint(f"Gimp #{i+1}", {'from': dev})

    gimpies.safeTransferFrom(dev, accounts[1], 8, {'from': dev})
    gimpies.safeTransferFrom(dev, accounts[1], 9, {'from': dev})
    gimpies.safeTransferFrom(dev, accounts[2], 10, {'from': dev})
    return gimpies

@pytest.fixture
def contracts(gimpies):
    dev = accounts[0]

    name = "Psychonauts Test"
    symbol = "PSYCO"
    base_uri = "base_uri/"
    base_extension = ".json"
    not_revealed_uri = "not revealed"
    mint_price = 1000000000000000000 # 1 ether
    max_supply = 10
    wallet = accounts[8]
    psychos = Psychonauts.deploy(
                            name,
                            symbol,
                            base_uri,
                            base_extension,
                            not_revealed_uri,
                            mint_price,
                            max_supply,
                            gimpies,
                            wallet,
                            {"from": dev}
                )
    return psychos, gimpies

def test_initial_state(contracts):
    psychos, gimpies = contracts

    assert accounts[0].balance() == "100 ether"
    assert gimpies.balanceOf(accounts[0]) == 7
    assert gimpies.balanceOf(accounts[1]) == 2
    assert gimpies.balanceOf(accounts[2]) == 1
    for i in range(3, 10):
        assert gimpies.balanceOf(accounts[i]) == 0

def test_valid_mint(contracts):
    psychos, gimpies = contracts
    psychos.revealPsychonauts()
    psychos.mintSwitch({"from": accounts[0]})
    initial_wallet_balance = accounts[8].balance()
    
    acc_0_balance = accounts[0].balance()
    token_ids = [4, 6, 5, 7]
    psychos.mint(token_ids, {"from": accounts[0], "value": "4 ether"})
    assert psychos.ownerOf(1) == accounts[0]
    assert psychos.ownerOf(2) == accounts[0]
    assert psychos.ownerOf(3) == accounts[0]
    assert psychos.ownerOf(4) == accounts[0]
    accounts[0].balance() == acc_0_balance - "4 ether"
    assert psychos.tokenURI(2) == "base_uri/2.json"

    acc_1_balance = accounts[1].balance()
    token_ids = [9, 8]
    psychos.mint(token_ids, {"from": accounts[1], "value": "2 ether"})
    assert psychos.ownerOf(5) == accounts[1]
    assert psychos.ownerOf(6) == accounts[1]
    accounts[1].balance() == acc_1_balance - "2 ether"

    acc_2_balance = accounts[2].balance()
    token_ids = [10]
    psychos.mint(token_ids, {"from": accounts[2], "value": "1 ether"})
    assert psychos.ownerOf(7) == accounts[2]
    accounts[2].balance() == acc_2_balance - "1 ether"

    acc_0_balance = accounts[0].balance()
    token_ids = [1, 2, 3]
    psychos.mint(token_ids, {"from": accounts[0], "value": "3 ether"})
    assert psychos.ownerOf(8) == accounts[0]
    assert psychos.ownerOf(9) == accounts[0]
    assert psychos.ownerOf(10) == accounts[0]
    accounts[0].balance() == acc_0_balance - "3 ether"


    assert accounts[8].balance() == initial_wallet_balance + "10 ether"
    assert psychos.totalSupply() == 10

    with brownie.reverts("Psychonauts: all tokens have been minted"):
        psychos.mint([1], {"from": accounts[2], "value": "1 ether"})


def test_only_admin(contracts):
    psychos, gimpies = contracts
    admins = [0, 8]
    rabbit_index = 0
    psychos.mintSwitch({"from": accounts[0]})
    psychos.mint([4, 5], {"from": accounts[0], "value": "2 ether"})
    for i in range(10):
        if i in admins:
            psychos.mintSwitch({"from": accounts[i]})
            psychos.setBaseURI("test/", {"from": accounts[i]})
            psychos.setBaseExtension(".jpg", {"from": accounts[i]})
            psychos.setTokenURI(1, "new tokenURI", {"from": accounts[i]})
            psychos.setPrice("2 ether", {"from": accounts[i]})
            psychos.revealPsychonauts({"from": accounts[i]})
        else:
            with brownie.reverts("Psychonauts: caller is not admin"):
                psychos.mintSwitch({"from": accounts[i]})
                psychos.setBaseURI("test/", {"from": accounts[i]})
                psychos.setBaseExtension(".jpg", {"from": accounts[i]})
                psychos.setTokenURI(1, "new tokenURI", {"from": accounts[i]})
                psychos.setPrice("0.5 ether", {"from": accounts[i]})
                psychos.revealPsychonauts({"from": accounts[i]})

def test_minting_closed(contracts):
    psychos, gimpies = contracts
    with brownie.reverts("Psychonauts: minting is currently not open"):
        psychos.mint([5, 6], {"from": accounts[0], "value": "2 ether"})

    psychos.mintSwitch({"from": accounts[0]})
    psychos.mint([5, 6], {"from": accounts[0], "value": "2 ether"})
    assert psychos.totalSupply() == 2

def test_invalid_mint_max_reached(contracts):
    psychos, gimpies = contracts
    psychos.revealPsychonauts()
    psychos.mintSwitch({"from": accounts[0]})

    psychos.mint([1, 2, 3, 4, 5, 6, 7], {"from": accounts[0], "value": "7 ether"})
    psychos.mint([8, 9], {"from": accounts[1], "value": "2 ether"})
    psychos.mint([10], {"from": accounts[2], "value": "1 ether"})

    with brownie.reverts("Psychonauts: all tokens have been minted"):
        psychos.mint([10], {"from": accounts[2], "value": "1 ether"})

def test_incorrect_mint_price(contracts):
    psychos, gimpies = contracts
    psychos.mintSwitch({"from": accounts[0]})
    token_ids_1 = [2, 3, 6]
    token_ids_2 = [9, 8]
    with brownie.reverts("Psychonauts: amount sent is incorrect"):
        psychos.mint(token_ids_1, {"from": accounts[0], "value": "2.9 ether"})
        psychos.mint(token_ids_2, {"from": accounts[1], "value": "1.9 ether"})
    with brownie.reverts("Psychonauts: amount sent is incorrect"):
        psychos.mint(token_ids_1, {"from": accounts[0], "value": "3.1 ether"})
        psychos.mint(token_ids_2, {"from": accounts[1], "value": "2.1 ether"})
    psychos.mint(token_ids_1, {"from": accounts[0], "value": "3 ether"})
    psychos.mint(token_ids_2, {"from": accounts[1], "value": "2 ether"})

def test_caller_is_not_owner(contracts):
    psychos, gimpies = contracts
    psychos.mintSwitch({"from": accounts[0]})
    token_ids = [4, 2, 7]

    with brownie.reverts("Psychonauts: caller is not owner of that Gimp"):
        psychos.mint([4, 2, 7], {"from": accounts[1], "value": "3 ether"})
        psychos.mint([4, 2, 8], {"from": accounts[0], "value": "3 ether"})

    psychos.mint([4, 2, 7], {"from": accounts[0], "value": "3 ether"})

def test_gimp_double_mint(contracts):
    psychos, gimpies = contracts
    psychos.mintSwitch({"from": accounts[0]})

    psychos.mint([4, 2, 7], {"from": accounts[0], "value": "3 ether"})
    assert psychos.hasGimpMintedPsychonaut(4) == True
    assert psychos.hasGimpMintedPsychonaut(2) == True
    assert psychos.hasGimpMintedPsychonaut(7) == True
    with brownie.reverts("Psychonauts: this Gimp has already minted a Psychonaut"):
        psychos.mint([4, 2, 7], {"from": accounts[0], "value": "3 ether"})

    gimpies.safeTransferFrom(accounts[0], accounts[1], 7)
    with brownie.reverts("Psychonauts: this Gimp has already minted a Psychonaut"):
        psychos.mint([8, 9, 7], {"from": accounts[1], "value": "3 ether"})
        psychos.mint([7], {"from": accounts[1], "value": "1 ether"})

    psychos.mint([8, 9], {"from": accounts[1], "value": "2 ether"})

def test_try_to_mint_too_many(contracts):
    psychos, gimpies = contracts
    psychos.mintSwitch({"from": accounts[0]})

    with brownie.reverts("Psychonauts: tried to mint too many"):
        psychos.mint(list(range(11)), {"from": accounts[0], "value": "11 ether"})

def test_change_mint_price(contracts):
    psychos, gimpies = contracts
    wallet_balance = accounts[8].balance()
    minter_balance = accounts[0].balance()
    psychos.mintSwitch({"from": accounts[0]})

    psychos.mint([4, 5, 6], {"from": accounts[0], "value": "3 ether"})
    psychos.setPrice("0.5 ether", {"from": accounts[8]})
    with brownie.reverts("Psychonauts: amount sent is incorrect"):
        psychos.mint([1, 2], {"from": accounts[0], "value": "2 ether"})

    psychos.mint([1, 2], {"from": accounts[0], "value": "1 ether"})

    psychos.setPrice("0 ether", {"from": accounts[8]})
    psychos.mint([3, 7], {"from": accounts[0]})

    assert accounts[0].balance() == minter_balance - "4 ether"
    assert accounts[8].balance() == wallet_balance + "4 ether"

def test_tokenURI(contracts):
    psychos, gimpies = contracts
    psychos.mintSwitch({"from": accounts[0]})

    # revert if token not minted yet
    with brownie.reverts("Psychonauts: URI query for nonexistent token"):
        psychos.tokenURI(1)

    psychos.mint([1, 2, 3, 4, 5, 6, 7], {"from": accounts[0], "value": "7 ether"})
    psychos.mint([8, 9], {"from": accounts[1], "value": "2 ether"})
    psychos.mint([10], {"from": accounts[2], "value": "1 ether"})

    # return not revealed URI
    assert psychos.tokenURI(1) == "not revealed"
    assert psychos.tokenURI(5) == "not revealed"
    assert psychos.tokenURI(10) == "not revealed"

    psychos.revealPsychonauts()
    assert psychos.tokenURI(1) == "base_uri/1.json"
    assert psychos.tokenURI(5) == "base_uri/5.json"
    assert psychos.tokenURI(10) == "base_uri/10.json"

    psychos.setTokenURI(1, "new #1", {"from": accounts[0]})
    psychos.setTokenURI(10, "new #10", {"from": accounts[8]})
    assert psychos.tokenURI(1) == "base_uri/" + "new #1"
    assert psychos.tokenURI(10) == "base_uri/" + "new #10"

    psychos.setBaseURI("", {"from": accounts[8]})
    assert psychos.tokenURI(1) == "new #1"
    assert psychos.tokenURI(10) == "new #10"
