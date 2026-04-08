//+------------------------------------------------------------------+
//|                                              SendTradeToDash.mqh |
//|                                    AlphaDash MT5 Integration     |
//|                                  Sends closed trades to API     |
//+------------------------------------------------------------------+
#property strict

// AlphaDash API Configuration
input string   AlphaDash_API_Url = "http://localhost:8000/api/ingest/";  // API endpoint URL
input int      AlphaDash_Account_Number = 0;                               // Account number (0 = auto-detect)
input string   AlphaDash_Broker_Name = "";                                 // Broker name (optional)
input bool     AlphaDash_Send_On_Close = true;                             // Send trades on close

// Global variables
string g_API_URL = "";
int g_AccountNumber = 0;

//+------------------------------------------------------------------+
//| Initialize AlphaDash connection                                  |
//+------------------------------------------------------------------+
bool AlphaDash_Init()
{
    g_API_URL = AlphaDash_API_Url;
    g_AccountNumber = (AlphaDash_Account_Number > 0) ? AlphaDash_Account_Number : (int)AccountInfoInteger(ACCOUNT_LOGIN);

    // Test connection
    Print("AlphaDash: Initializing for account ", g_AccountNumber);
    Print("AlphaDash: API URL = ", g_API_URL);

    return true;
}

//+------------------------------------------------------------------+
//| Send closed trade to AlphaDash API                                |
//+------------------------------------------------------------------+
bool SendTradeToDash(ulong ticket)
{
    // Get trade data
    if(!HistoryDealSelect(ticket))
    {
        Print("AlphaDash: Failed to select deal ", ticket);
        return false;
    }

    // Get deal properties
    ENUM_DEAL_TYPE dealType = (ENUM_DEAL_TYPE)HistoryDealGetInteger(ticket, DEAL_TYPE);
    ENUM_DEAL_ENTRY dealEntry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY);

    // Only process closing deals (DEAL_ENTRY_OUT or DEAL_ENTRY_OUT_BY)
    if(dealEntry != DEAL_ENTRY_OUT && dealEntry != DEAL_ENTRY_OUT_BY)
    {
        return false; // Not a closing deal
    }

    // Get position properties
    ulong positionTicket = HistoryDealGetInteger(ticket, DEAL_POSITION_ID);

    // Find the opening deal to get full position info
    ulong openTicket = 0;
    double openPrice = 0;
    datetime openTime = 0;
    double sl = 0;
    double tp = 0;
    int magic = 0;
    string symbol = HistoryDealGetString(ticket, DEAL_SYMBOL);
    double volume = HistoryDealGetDouble(ticket, DEAL_VOLUME);

    // Search for position opening deal
    int totalDeals = HistoryDealsTotal();
    for(int i = 0; i < totalDeals; i++)
    {
        ulong dealTicket = HistoryDealGetTicket(i);
        if(HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID) == positionTicket)
        {
            ENUM_DEAL_ENTRY entryType = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
            if(entryType == DEAL_ENTRY_IN || entryType == DEAL_ENTRY_INOUT)
            {
                openTicket = dealTicket;
                openPrice = HistoryDealGetDouble(dealTicket, DEAL_PRICE);
                openTime = (datetime)HistoryDealGetInteger(dealTicket, DEAL_TIME);
                magic = (int)HistoryDealGetInteger(dealTicket, DEAL_MAGIC);
                sl = 0; // SL/TP need to be retrieved from position history
                tp = 0;
                break;
            }
        }
    }

    // Get closing properties
    double closePrice = HistoryDealGetDouble(ticket, DEAL_PRICE);
    datetime closeTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
    double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
    double commission = HistoryDealGetDouble(ticket, DEAL_COMMISSION);
    double swap = HistoryDealGetDouble(ticket, DEAL_SWAP);

    // Calculate trade type (Buy/Sell)
    ENUM_DEAL_TYPE positionType = dealType;
    string tradeType = (positionType == DEAL_TYPE_BUY) ? "Buy" : "Sell";

    // Calculate pips
    double pips = CalculatePips(openPrice, closePrice, symbol, tradeType);

    // Calculate MAE/MFE (simplified - would need position history for accurate values)
    double mae = 0; // Maximum Adverse Excursion
    double mfe = 0; // Maximum Favorable Excursion

    // Build JSON payload
    string json = BuildTradeJSON(
        ticket,
        positionType,
        symbol,
        volume,
        openTime,
        closeTime,
        openPrice,
        closePrice,
        sl,
        tp,
        profit,
        commission,
        swap,
        pips,
        magic,
        mae,
        mfe
    );

    // Send to API
    return SendToAPI(json);
}

//+------------------------------------------------------------------+
//| Build JSON payload for trade data                                 |
//+------------------------------------------------------------------+
string BuildTradeJSON(
    ulong ticket,
    ENUM_DEAL_TYPE dealType,
    string symbol,
    double volume,
    datetime openTime,
    datetime closeTime,
    double openPrice,
    double closePrice,
    double sl,
    double tp,
    double profit,
    double commission,
    double swap,
    double pips,
    int magic,
    double mae,
    double mfe
)
{
    string json = "{";

    // Core trade data
    json += "\"ticket_id\":" + IntegerToString(ticket) + ",";
    json += "\"account_number\":" + IntegerToString(g_AccountNumber) + ",";
    json += "\"magic_number\":" + IntegerToString(magic) + ",";
    json += "\"symbol\":\"" + symbol + "\",";
    json += "\"type\":\"" + ((dealType == DEAL_TYPE_BUY) ? "Buy" : "Sell") + "\",";
    json += "\"lots\":" + DoubleToString(volume, 2) + ",";

    // Timestamps in ISO 8601 format
    json += "\"open_time\":\"" + TimeToISO8601(openTime) + "\",";
    json += "\"close_time\":\"" + TimeToISO8601(closeTime) + "\",";

    // Prices
    json += "\"open_price\":" + DoubleToString(openPrice, 8) + ",";
    json += "\"close_price\":" + DoubleToString(closePrice, 8) + ",";
    json += "\"sl\":" + (sl > 0 ? DoubleToString(sl, 8) : "null") + ",";
    json += "\"tp\":" + (tp > 0 ? DoubleToString(tp, 8) : "null") + ",";

    // Results
    json += "\"profit_usd\":" + DoubleToString(profit, 2) + ",";
    json += "\"pips\":" + DoubleToString(pips, 1) + ",";
    json += "\"commission\":" + DoubleToString(commission, 2) + ",";
    json += "\"swap\":" + DoubleToString(swap, 2) + ",";
    json += "\"mae\":" + DoubleToString(mae, 2) + ",";
    json += "\"mfe\":" + DoubleToString(mfe, 2);

    // Broker info (optional)
    if(AlphaDash_Broker_Name != "")
    {
        json += ",\"broker_name\":\"" + AlphaDash_Broker_Name + "\"";
    }

    json += "}";

    return json;
}

//+------------------------------------------------------------------+
//| Convert datetime to ISO 8601 string                               |
//+------------------------------------------------------------------+
string TimeToISO8601(datetime dt)
{
    MqlDateTime tm;
    TimeToStruct(dt, tm);

    return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",
        tm.year, tm.mon, tm.day, tm.hour, tm.min, tm.sec);
}

//+------------------------------------------------------------------+
//| Calculate pips based on symbol type                               |
//+------------------------------------------------------------------+
double CalculatePips(double openPrice, double closePrice, string symbol, string tradeType)
{
    double pipMultiplier = 0.0001; // Default for standard forex

    // JPY pairs
    if(StringFind(symbol, "JPY") >= 0)
    {
        pipMultiplier = 0.01;
    }
    // Indices (approximate)
    else if(StringFind(symbol, "US") == 0 || StringFind(symbol, "GER") == 0 ||
            StringFind(symbol, "UK") == 0 || StringFind(symbol, "JP") == 0)
    {
        pipMultiplier = 0.1;
    }
    // Crypto
    else if(StringFind(symbol, "BTC") >= 0 || StringFind(symbol, "ETH") >= 0)
    {
        pipMultiplier = 0.01;
    }
    // Gold/Silver
    else if(StringFind(symbol, "XAU") >= 0 || StringFind(symbol, "XAG") >= 0)
    {
        pipMultiplier = 0.01;
    }

    double priceDiff = closePrice - openPrice;

    // Invert for sell trades
    if(tradeType == "Sell")
    {
        priceDiff = -priceDiff;
    }

    return priceDiff / pipMultiplier;
}

//+------------------------------------------------------------------+
//| Send JSON payload to API via WebRequest                           |
//+------------------------------------------------------------------+
bool SendToAPI(string json)
{
    // Prepare headers
    string headers = "Content-Type: application/json\r\n";
    headers += "Accept: application/json\r\n";

    // Response variables
    string response = "";
    int timeout = 5000; // 5 second timeout

    // Debug output
    Print("AlphaDash: Sending trade data...");
    Print("AlphaDash: JSON = ", json);

    // Send POST request
    int result = WebRequest(
        "POST",
        g_API_URL,
        headers,
        timeout,
        json,
        response,
        result
    );

    // Check result
    if(result == -1)
    {
        int errorCode = GetLastError();
        Print("AlphaDash: WebRequest failed with error ", errorCode);
        Print("AlphaDash: Error description: ", ErrorDescription(errorCode));

        // Common issues:
        // 4056 - URL not in allowed list (add to Tools > Options > Expert Advisors > Allow WebRequest for URLs)
        // 4060 - Network error

        return false;
    }

    // Check HTTP status code
    if(result != 200)
    {
        Print("AlphaDash: HTTP error ", result);
        Print("AlphaDash: Response = ", response);
        return false;
    }

    Print("AlphaDash: Trade sent successfully");
    Print("AlphaDash: Response = ", response);

    return true;
}

//+------------------------------------------------------------------+
//| Get error description                                             |
//+------------------------------------------------------------------+
string ErrorDescription(int errorCode)
{
    switch(errorCode)
    {
        case 4056: return "URL not in allowed list. Add URL to Tools > Options > Expert Advisors > Allow WebRequest";
        case 4060: return "Network error";
        case 4061: return "Invalid parameters";
        case 4062: return "Invalid handle";
        case 4063: return "Timeout";
        default: return "Unknown error";
    }
}

//+------------------------------------------------------------------+
//| Process all closed positions (for history import)                 |
//+------------------------------------------------------------------+
int AlphaDash_SendHistory(datetime fromTime, datetime toTime)
{
    // Select history
    if(!HistorySelect(fromTime, toTime))
    {
        Print("AlphaDash: Failed to select history");
        return 0;
    }

    int totalDeals = HistoryDealsTotal();
    int sentCount = 0;

    Print("AlphaDash: Processing ", totalDeals, " deals...");

    for(int i = 0; i < totalDeals; i++)
    {
        ulong dealTicket = HistoryDealGetTicket(i);
        if(dealTicket > 0)
        {
            if(SendTradeToDash(dealTicket))
            {
                sentCount++;
            }

            // Small delay to avoid overwhelming the API
            Sleep(100);
        }
    }

    Print("AlphaDash: Sent ", sentCount, " trades");
    return sentCount;
}

//+------------------------------------------------------------------+
//| Batch send multiple trades                                        |
//+------------------------------------------------------------------+
bool AlphaDash_SendBatch(string jsonArray)
{
    string headers = "Content-Type: application/json\r\n";
    headers += "Accept: application/json\r\n";

    string response = "";
    int timeout = 30000; // 30 second timeout for batch

    string url = g_API_URL + "batch";

    int result = WebRequest(
        "POST",
        url,
        headers,
        timeout,
        jsonArray,
        response,
        result
    );

    if(result != 200)
    {
        Print("AlphaDash: Batch send failed with status ", result);
        return false;
    }

    Print("AlphaDash: Batch sent successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Example usage in OnDeinit for sending trades on close             |
//+------------------------------------------------------------------+
/*
// In your EA's OnTick or OnTradeTransaction:

void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
    if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
    {
        ENUM_DEAL_TYPE dealType = (ENUM_DEAL_TYPE)HistoryDealGetInteger(trans.deal, DEAL_TYPE);
        ENUM_DEAL_ENTRY dealEntry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);

        // Only send closing deals
        if(dealEntry == DEAL_ENTRY_OUT || dealEntry == DEAL_ENTRY_OUT_BY)
        {
            if(AlphaDash_Send_On_Close)
            {
                SendTradeToDash(trans.deal);
            }
        }
    }
}

// In OnInit:
int OnInit()
{
    if(!AlphaDash_Init())
    {
        Print("AlphaDash: Initialization failed");
        return INIT_FAILED;
    }

    return INIT_SUCCEEDED;
}
*/

//+------------------------------------------------------------------+