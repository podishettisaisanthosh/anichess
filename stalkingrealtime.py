import asyncio
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

from tradingbot import place_order

# -----------------------------
# CONFIG
# -----------------------------
RPC_URL = "https://mainnet.base.org"
WALLET = "0x6cC148A7aDbc2EFadDED8e0E9A86f6FAF3678CbA".lower()
POLL_INTERVAL = 2

APPROVE_SELECTOR = "095ea7b3"

# -----------------------------
# CONNECT
# -----------------------------
w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))

# -----------------------------
# HELPERS
# -----------------------------
def normalize_input(tx_input):
    if isinstance(tx_input, bytes):
        return tx_input.hex()
    return tx_input

def classify_tx(tx, code_cache):
    tx_input = normalize_input(tx["input"])

    if tx_input.startswith(APPROVE_SELECTOR):
        return "APPROVE"

    to_addr = tx["to"]
    if to_addr:
        if to_addr not in code_cache:
            code_cache[to_addr] = True  # assume contract
        if tx_input != "0x":
            return "EXECUTE"

    return "TRANSFER"

def decode_approve_manual(tx):
    tx_input = normalize_input(tx["input"])[8:]
    spender = "0x" + tx_input[:64][24:]
    amount = int(tx_input[64:128], 16)
    return spender, amount

async def get_token_info(token_address):
    try:
        erc20 = w3.eth.contract(
            address=token_address,
            abi=[
                {"name": "symbol", "outputs": [{"type": "string"}], "inputs": [], "stateMutability": "view", "type": "function"},
                {"name": "decimals", "outputs": [{"type": "uint8"}], "inputs": [], "stateMutability": "view", "type": "function"},
            ]
        )
        symbol = await erc20.functions.symbol().call()
        return symbol
    except:
        return "UNKNOWN"

# -----------------------------
# MAIN LOOP
# -----------------------------
async def monitor_wallet():
    flag=[False]
    print("Connected to Base (async)")
    print("Monitoring wallet:", WALLET)

    last_block = await w3.eth.block_number
    code_cache = {}

    while True:
        latest_block = await w3.eth.block_number

        if latest_block > last_block:
            for block_number in range(last_block + 1, latest_block + 1):
                block = await w3.eth.get_block(block_number, full_transactions=True)

                for tx in block.transactions:
                    frm = tx["from"].lower()
                    to = tx["to"].lower() if tx["to"] else None

                    if frm == WALLET or to == WALLET:
                        tx_type = classify_tx(tx, code_cache)

                        print("\n=== NEW TX ===")
                        print("Block:", block_number)
                        print("Hash:", tx["hash"].hex())
                        print("Type:", tx_type)


                        if tx_type == "APPROVE":
                            #spender, amount = decode_approve_manual(tx)
                            symbol= await get_token_info(tx["to"])
                            #print(f"APPROVED {amount / (10 ** decimals)} {symbol}")
                            #print("Spender:", spender)
                            if (symbol != "CHECK"):
                                print("placing buy order")
                                place_order("buy")
                                print("Symbol not check")
                                flag[0]=True


                        elif tx_type == "EXECUTE":
                            if(flag):
                                place_order("sell")
                            print("Executed contract:", to)

                        else:
                            print("Transfer:", w3.from_wei(tx["value"], "ether"), "ETH")

            last_block = latest_block

        await asyncio.sleep(POLL_INTERVAL)

# -----------------------------
# RUN
# -----------------------------
asyncio.run(monitor_wallet())
