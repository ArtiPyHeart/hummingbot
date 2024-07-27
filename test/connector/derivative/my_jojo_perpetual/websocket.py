import asyncio
from test.connector.derivative.my_jojo_perpetual.rest_api import PRIVATE_KEY, PUBLIC_KEY, auth, time_sync
from urllib.parse import urljoin

import websockets
from furl import furl

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants import (
    PERPETUAL_WS_URL,
    WS_SINGLE_URL,
)

if __name__ == "__main__":

    async def run_websocket():
        account = PUBLIC_KEY
        uri = furl(urljoin(PERPETUAL_WS_URL, WS_SINGLE_URL))
        uri /= f"account@{account}"
        timestamp = int(time_sync.time() * 1e3)
        sign = auth.sign_message(
            PRIVATE_KEY,
            account=account,
            timestamp=timestamp,
        )
        uri.args["timestamp"] = timestamp
        uri.args["signature"] = sign

        async with websockets.connect(uri.url) as websocket:
            # 接收数据
            while True:
                response = await websocket.recv()
                print(f"Received: {response}")

    # 运行异步函数
    asyncio.get_event_loop().run_until_complete(run_websocket())
    """
    Sent: {'id': 1, 'method': 'SUBSCRIBE', 'params': ['btcusdc@orderbook', 'btcusdc@market', 'btcusdc@trades']}
    Received: {"result":null,"id":1}
    Received: {"stream":"btcusdc@orderbook","data":{"event":"snapshot","sequence":171602075,"bids":[["66626.71","1.0506"],["66626.41","1.0506"],["66625.04","1.1236"],["66623.37","1.1401"],["66621.71","1.1569"],["66620.04","1.1739"],["66618.38","1.1911"],["66616.71","1.2086"],["66615.05","1.2264"],["66613.38","1.2444"],["66611.72","1.2627"],["66610.05","1.2813"],["66609.75","1.2813"],["66608.05","0.9383"],["66606.05","0.9384"],["66605.75","0.9384"],["66604.06","0.9384"],["66602.06","0.9384"],["66601.76","0.9384"],["66600.06","0.9384"],["66599.76","0.9384"],["66598.06","0.9385"],["66596.06","0.9385"],["66594.07","0.9385"],["66592.07","0.9386"],["66591.77","0.9386"],["66590.07","0.9386"],["66589.77","0.9386"],["66588.07","0.9386"],["66587.77","0.9386"],["66586.08","0.9386"],["66585.78","0.9386"],["66584.08","0.9387"],["66583.78","0.9387"],["66580.08","0.9387"],["66579.78","0.9387"],["66578.09","0.9387"],["66577.79","0.9388"],["66575.79","0.9388"],["66573.79","0.9388"],["66571.79","0.9388"],["66569.8","0.9389"],["66400","0.000461"],["66399.99","0.003761"],["66305.96","0.000405"],["66300","0.0004"],["66200","0.000461"],["66185.29","0.0004"],["66154.76","0.001662"],["66142.85","0.003761"],["66043.04","0.000568"],["66000","0.001289"],["65985.43","0.000405"],["65911.01","4.4606"],["65910.71","4.4606"],["65891.17","0.0004"],["65885.71","0.003761"],["65837.7","0.001662"],["65800","0.000461"],["65750","0.000661"],["65733.33","0.0004"],["65700","0.0004"],["65664.91","0.000405"],["65628.57","0.003761"],["65619.56","0.000568"],["65600","0.000461"],["65597.05","0.0004"],["65520.64","0.001662"],["65500","0.001089"],["65466.66","0.0004"],["65400","0.000861"],["65371.42","0.003761"],["65344.38","0.000405"],["65302.94","0.0004"],["65258.15","4.5052"],["65250","0.000661"],["65203.58","0.001662"],["65200","0.000861"],["65196.08","0.000568"],["65114.28","0.003761"],["65100","0.0004"],["65023.86","0.000405"],["65008.82","0.0004"],["65000","0.00155"],["64933.33","0.0004"],["64886.53","0.001662"],["64857.14","0.003761"],["64800","0.000861"],["64772.6","0.000568"],["64750","0.000661"],["64714.7","0.0004"],["64703.33","0.000405"],["64666.66","0.0004"],["64612.05","4.5502"],["64600","0.000461"],["64599.99","0.003761"],["64569.47","0.001662"],["64500","0.001489"],["64420.58","0.0004"],["64400","0.000861"],["64382.81","0.000405"],["64349.12","0.000568"],["64342.85","0.003761"],["64252.41","0.001662"],["64250","0.000661"],["64200","0.000861"],["64133.33","0.0004"],["64126.47","0.0004"],["64085.71","0.003761"],["64062.28","0.000405"],["64000","0.00155"],["63972.35","4.5957"],["63935.35","0.001662"],["63925.64","0.000568"],["63900","0.0004"],["63866.66","0.0004"],["63832.35","0.0004"],["63828.57","0.003761"],["63800","0.000461"],["63750","0.000661"],["63741.76","0.000405"],["63618.29","0.001662"],["63600","0.001261"],["63571.42","0.003761"],["63538.23","0.0004"],["63502.16","0.000568"],["63500","0.001089"],["63421.23","0.000405"],["63400","0.000461"],["63333.33","0.0004"],["63314.28","0.003761"],["63301.24","0.001662"],["63300","0.0004"],["63250","0.000661"],["63244.11","0.0004"],["63200","0.000461"],["63100.71","0.000405"],["63078.68","0.000568"],["63066.66","0.0004"],["63057.14","0.003761"],["63000","0.00195"],["62984.18","0.001662"],["62950","0.0004"],["62800","0.000861"],["62799.99","0.003761"],["62780.19","0.000405"],["62750","0.000661"],["62711.88","4.6881"],["62700","0.0004"],["62667.12","0.001662"],["62655.2","0.000568"],["62600","0.000461"],["62542.85","0.003761"],["62533.33","0.0004"],["62500","0.001089"],["62459.66","0.000405"],["62450","0.040832"],["62400","0.000861"],["62350.06","0.001662"],["62285.71","0.003761"],["62266.66","0.0004"],["62250","0.000661"],["62200","0.000461"],["62139.14","0.000405"],["62100","0.0004"],["62091","4.735"],["62033.01","0.001662"],["62028.57","0.003761"],["62000","0.00195"],["61818.61","0.000405"],["61800","0.000861"],["61771.42","0.003761"],["61750","0.000661"],["61715.95","0.001662"],["61600","0.000461"],["61514.28","0.003761"],["61500","0.001489"],["61498.09","0.000405"],["61476.53","4.7823"],["61476.25","4.7823"],["61400","0.000461"],["61398.89","0.001662"],["61257.14","0.003761"],["61250","0.000661"],["61200","0.000861"],["61177.56","0.000405"],["61081.83","0.001662"],["61000","0.00155"],["60999.99","0.003761"],["60900","0.0004"],["60867.6","4.8302"],["60857.04","0.000405"],["60800","0.000461"],["60764.78","0.001662"],["60750","0.000661"],["60742.85","0.003761"],["60600","0.000861"],["60536.51","0.000405"],["60500","0.001089"],["60485.71","0.003761"]],"asks":[["81389.88","3.6122"],["80584.07","3.6484"],["79786.23","3.6848"],["78996.3","3.7217"],["78214.18","3.7589"],["76673.1","3.8345"],["75913.99","3.8728"],["75000","0.000861"],["74800","0.000461"],["74700","0.0004"],["74639.6","0.000405"],["74600","0.000461"],["74418.57","3.9506"],["74418.23","3.9506"],["74400","0.000861"],["74319.07","0.000405"],["74200","0.000461"],["74100","0.0004"],["74000","0.000461"],["73998.55","0.000405"],["73800","0.000861"],["73681.44","3.9901"],["73678.02","0.000405"],["73600","0.000461"],["73500","0.0004"],["73400","0.000461"],["73357.5","0.000405"],["73200","0.000861"],["73036.97","0.000405"],["73000","0.000461"],["72900","0.0004"],["72800","0.000461"],["72716.45","0.000405"],["72600","0.000861"],["72400","0.000461"],["72395.92","0.000405"],["72300","0.0004"],["72230","4.0703"],["72229.68","4.0703"],["72200","0.000461"],["72075.4","0.000405"],["72000","0.000861"],["71861.79","0.001662"],["71800","0.000461"],["71754.87","0.000405"],["71700","0.0004"],["71600","0.000461"],["71544.74","0.001662"],["71434.35","0.000405"],["71400","0.000861"],["71227.68","0.001662"],["71200","0.000461"],["71113.82","0.000405"],["71100","0.0004"],["71000","0.000461"],["70910.62","0.001662"],["70806.51","4.1522"],["70800","0.000861"],["70793.3","0.000405"],["70600","0.000461"],["70593.56","0.001662"],["70500","0.0004"],["70472.78","0.000405"],["70400","0.000461"],["70276.51","0.001662"],["70200","0.000861"],["70152.25","0.000405"],["70000","0.000889"],["69999.99","0.003761"],["69959.45","0.001662"],["69900","0.0004"],["69831.73","0.000405"],["69800","0.000461"],["69777","0.429941"],["69742.85","0.003761"],["69642.39","0.001662"],["69600","0.000861"],["69511.2","0.000405"],["69500","0.000428"],["69485.71","0.003761"],["69411.39","4.2356"],["69400","0.000461"],["69325.33","0.001662"],["69300","0.0004"],["69228.57","0.003761"],["69200","0.000461"],["69190.68","0.000405"],["69008.28","0.001662"],["69000","0.001289"],["68971.42","0.003761"],["68870.15","0.000405"],["68800","0.000461"],["68724.17","4.278"],["68714.28","0.003761"],["68700","0.0004"],["68691.22","0.001662"],["68600","0.000461"],["68549.63","0.000405"],["68500","0.000428"],["68457.14","0.003761"],["68400","0.000861"],["68374.16","0.001662"],["68229.1","0.000405"],["68200","0.000461"],["68199.99","0.003761"],["68100","0.0004"],["68057.1","0.001662"],["68044.06","4.3207"],["68043.76","4.3207"],["68000","0.000889"],["67950","0.0004"],["67942.85","0.003761"],["67908.58","0.000405"],["67800","0.000861"],["67740.04","0.001662"],["67685.71","0.003761"],["67655.88","0.0004"],["67600","0.000461"],["67588.05","0.000405"],["67500","0.000828"],["67428.57","0.003761"],["67422.99","0.001662"],["67400","0.000461"],["67370.08","4.364"],["67361.76","0.0004"],["67267.53","0.000405"],["67200","0.000861"],["67171.42","0.003761"],["67105.93","0.001662"],["67067.64","0.0004"],["67000","0.000889"],["66947","0.000405"],["66914.28","0.003761"],["66900","0.0004"],["66890","0.000568"],["66800","0.000461"],["66788.87","0.001662"],["66773.52","0.0004"],["66703.07","0.937"],["66701.37","0.937"],["66701.07","0.937"],["66699.07","0.937"],["66697.07","0.9371"],["66695.37","0.9371"],["66695.07","0.9371"],["66693.07","0.9371"],["66691.06","0.9372"],["66689.36","0.9372"],["66689.06","0.9372"],["66687.36","0.9372"],["66687.06","0.9372"],["66685.06","0.9372"],["66683.36","0.9373"],["66683.06","0.9373"],["66681.36","0.9373"],["66681.06","0.9373"],["66679.36","0.9373"],["66679.06","0.9373"],["66677.36","0.9373"],["66677.06","0.9374"],["66675.36","0.9374"],["66675.06","0.9374"],["66673.36","0.9374"],["66673.06","0.9374"],["66671.36","0.9374"],["66671.06","0.9374"],["66669.36","0.9375"],["66669.06","0.9375"],["66667.36","0.9375"],["66667.06","0.9375"],["66665.36","0.9375"],["66665.06","0.9375"],["66663.36","1.2802"],["66663.06","1.2802"],["66661.69","1.2618"],["66661.39","1.2618"],["66660.03","1.2435"],["66658.36","1.2256"],["66658.06","1.2256"],["66656.69","1.2079"],["66656.39","1.2079"],["66655.03","1.1905"],["66654.73","1.1905"],["66653.36","1.1733"],["66653.06","1.1733"],["66651.7","1.1563"],["66651.4","1.1563"],["66650.03","1.1396"],["66648.36","1.1232"],["66648.06","1.1232"],["66646.7","1.0503"],["66646.4","1.0503"]]}}
    Received: {"stream":"btcusdc@orderbook","data":{"event":"update","beginSequence":171602076,"endSequence":171602093,"bids":[["66609.75","0"],["66605.75","0"],["66601.76","0"],["66599.76","0"],["66591.77","0"],["66589.77","0"],["66587.77","0"],["66585.78","0"],["66583.78","0"],["66579.78","0"],["66573.79","0"],["60867.6","0"],["60447.72","0.001662"],["60400","0.000461"],["60300","0.0004"],["60228.57","0.003761"],["60215.99","0.000405"],["60200","0.000461"],["60130.66","0.001662"],["60000","0.042121"],["59971.42","0.003761"],["59895.46","0.000405"],["59813.6","0.001662"],["59800","0.000461"]],"asks":[["79786.23","0"],["75913.99","0"],["72229.68","0"],["66699.07","0"]]}}
    Received: {"stream":"btcusdc@orderbook","data":{"event":"update","beginSequence":171602094,"endSequence":171602145,"bids":[["66582.08","0.9387"],["66577.79","0"],["66576.09","0.9388"],["66575.79","0"],["66574.09","0.9388"],["66572.09","0.9388"],["66571.79","0"],["66570.1","0.9389"],["66569.8","0"],["65258.45","4.5052"],["64612.34","4.5502"],["64612.05","0"],["63972.64","4.5957"],["63339.27","4.6417"],["62712.17","4.6881"],["62091.28","4.735"],["60867.87","4.8301"],["60200","0"],["60130.66","0"],["60000","0"],["59971.42","0"],["59895.46","0"],["59813.6","0"],["59800","0"]],"asks":[["81390.25","3.6122"],["81389.88","0"],["80584.07","0"],["78996.3","0"],["77440.16","3.7965"],["76673.1","0"],["74418.23","0"],["73681.77","3.9901"],["73681.44","0"],["72952.28","4.03"],["71514.88","4.111"],["70806.83","4.1521"],["70806.51","0"],["70105.8","4.1937"],["69411.7","4.2356"],["69411.39","0"],["68724.48","4.278"],["68043.76","0"],["67370.38","4.3639"],["67370.08","0"],["66703.37","0.937"],["66699.37","0.937"],["66697.37","0.9371"],["66693.37","0.9371"],["66691.36","0.9372"],["66685.36","0.9372"],["66654.73","0"]]}}
    Received: {"stream":"btcusdc@market","data":{"fundingRate":"0.0001","nextFundingTime":1721491200000,"markPrice":"66677.90529265","offchainMarkPrice":"66631.10136888","offchainMarkPrice24HAgo":"63426.71921227","indexPrice":"66660.28041377","liquidationThreshold":"0.01","liquidationPriceOff":"0.005","24hVolume":"334.097258","24hQuoteVolume":"22005169.9984119","openInterest":"15.1628295","price24HAgo":"63512.25","lastTradePrice":"66629.63"}}
    Received: {"stream":"btcusdc@orderbook","data":{"event":"update","beginSequence":171602146,"endSequence":171602164,"bids":[["60265.24","4.8784"],["60215.99","0"]],"asks":[["80584.43","3.6483"],["79786.59","3.6848"],["78996.65","3.7217"],["78214.53","3.7589"],["76673.45","3.8344"],["75914.33","3.8728"],["75162.73","3.9115"],["66691.06","0"],["66687.06","0"],["66675.06","0"],["66651.4","0"]]}}
    Received: {"stream":"btcusdc@market","data":{"fundingRate":"0.0001","nextFundingTime":1721491200000,"markPrice":"66677.90529265","offchainMarkPrice":"66631.20097197","offchainMarkPrice24HAgo":"63426.71921227","indexPrice":"66660.59346744","liquidationThreshold":"0.01","liquidationPriceOff":"0.005","24hVolume":"334.097258","24hQuoteVolume":"22005169.9984119","openInterest":"15.1628295","price24HAgo":"63512.25","lastTradePrice":"66629.63"}}
    Received: {"stream":"btcusdc@orderbook","data":{"event":"update","beginSequence":171602165,"endSequence":171602192,"bids":[["65910.71","0"],["65258.15","0"],["63972.35","0"],["62711.88","0"],["62091","0"],["61476.25","0"],["60215.99","0.000405"],["60200","0.000461"],["60130.66","0.001662"],["60000","0.042121"],["59971.42","0.003761"],["59895.46","0.000405"]],"asks":[["78214.18","0"],["68724.17","0"],["66703.07","0"],["66701.07","0"],["66697.07","0"],["66695.07","0"],["66693.07","0"],["66689.06","0"],["66685.06","0"],["66683.06","0"],["66679.06","0"],["66677.06","0"],["66671.06","0"],["66667.06","0"],["66661.39","0"],["66658.06","0"],["66656.39","0"],["66653.06","0"],["66648.06","0"],["66646.4","0"]]}}
    Received: {"stream":"btcusdc@market","data":{"fundingRate":"0.0001","nextFundingTime":1721491200000,"markPrice":"66677.90529265","offchainMarkPrice":"66631.52021572","offchainMarkPrice24HAgo":"63426.71921227","indexPrice":"66660.28400431","liquidationThreshold":"0.01","liquidationPriceOff":"0.005","24hVolume":"334.097258","24hQuoteVolume":"22005169.9984119","openInterest":"15.1628295","price24HAgo":"63512.25","lastTradePrice":"66629.63"}}
    Received: {"stream":"btcusdc@market","data":{"fundingRate":"0.0001","nextFundingTime":1721491200000,"markPrice":"66677.90529265","offchainMarkPrice":"66631.21674049","offchainMarkPrice24HAgo":"63426.71921227","indexPrice":"66660.28400431","liquidationThreshold":"0.01","liquidationPriceOff":"0.005","24hVolume":"334.097258","24hQuoteVolume":"22005169.9984119","openInterest":"15.1628295","price24HAgo":"63512.25","lastTradePrice":"66629.63"}}
    Received: {"stream":"btcusdc@market","data":{"fundingRate":"0.0001","nextFundingTime":1721318400000,"markPrice":"63957.19635104","offchainMarkPrice":"63914.23080265","offchainMarkPrice24HAgo":"64984.01218979","indexPrice":"63948.18176244","liquidationThreshold":"0.01","liquidationPriceOff":"0.005","24hVolume":"359.939966","24hQuoteVolume":"23228879.5581368","openInterest":"17.9668545","price24HAgo":"65005.3","lastTradePrice":"63917.08"}}
    Received: {"stream":"btcusdc@trades","data":{"id":200299297171968,"price":"66657.35","amount":"0.184159","quoteAmount":"12275.55091865","time":1721461195599,"isBuyerMaker":false,"status":"CREATED"}}
    noqa: mock
    Received: {"event":"DEGEN_ACCOUNT_STATE_UPDATE","accountState":{"account":"","takeProfitRatioLimit":"200","positionMarginLimit":"10","assets":{"creditAmount":"0.007926","pendingCreditAmount":"0"},"positions":null}}
    Received: {"event":"ACCOUNT_UPDATE","balances":{"primaryCreditAmount":"1.43","positionMargin":"0","availableCreditAmounts":{"dogeusdc":{"buy":"14.3","sell":"14.3"},"ckbusdc":{"buy":"14.3","sell":"14.3"},"linkusdc":{"buy":"14.3","sell":"14.3"},"tiausdc":{"buy":"14.3","sell":"14.3"},"ondousdc":{"buy":"14.3","sell":"14.3"},"memeusdc":{"buy":"14.3","sell":"14.3"},"rndrusdc":{"buy":"14.3","sell":"14.3"},"enausdc":{"buy":"14.3","sell":"14.3"},"solusdc":{"buy":"35.75","sell":"35.75"},"xaiusdc":{"buy":"14.3","sell":"14.3"},"tonusdc":{"buy":"14.3","sell":"14.3"},"wusdc":{"buy":"14.3","sell":"14.3"},"btcusdc":{"sell":"71.5","buy":"71.5"},"trumpwinusdc":{"sell":"2.86","buy":"2.86"},"wifusdc":{"buy":"14.3","sell":"14.3"},"ethusdc":{"buy":"71.5","sell":"71.5"},"wldusdc":{"buy":"14.3","sell":"14.3"},"notusdc":{"buy":"14.3","sell":"14.3"},"ethfiusdc":{"sell":"14.3","buy":"14.3"},"ordiusdc":{"buy":"14.3","sell":"14.3"},"altusdc":{"buy":"14.3","sell":"14.3"},"bomeusdc":{"buy":"14.3","sell":"14.3"}},"secondaryCreditAmount":"0","pendingWithdrawPrimaryCreditAmount":"0","netValue":"1.43","leverage":"0.000000","frozenMargin":"0","isSafe":true,"lastUpdatedBlockNumber":17346940,"pendingWithdrawSecondaryCreditAmount":"0","exposure":"0","marginRate":"10000.000000","availableMargin":"1.43","availableWithdrawAmount":"1.43","perpetualBalances":{}},"positions":[]}
    """
