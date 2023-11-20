from django.shortcuts import render
from .models import *
from django.http import JsonResponse
from django .http import HttpResponse
from openpyxl import load_workbook
import pymssql
import pandas as pd
import json
from django.db.models import Sum, Min
from django.views import View
from rest_framework import viewsets,filters
from .serializers import *
from django_filters.rest_framework  import DjangoFilterBackend
from django.db import connections

class SqlDb:
    def __init__(self, database_name='default'):
        print("database_name : ",database_name)
        self.conn = connections[database_name]
        self.cursor = self.conn.cursor() 
       
 
def Login(request):
    context = {}
    print("This User Name : ", request.POST.get('Username'))
    if request.method == "POST":
        Username = request.POST.get('Username')
        pswd = request.POST.get('Password')
        if ManageUser.objects.filter(UserName=Username, Password=pswd).exists():
            if ManageUser.objects.filter(UserName=Username, LoginStatus = "True").exists():
                print("welcome")
            else:
                print("Already Login")
            request.session['Username'] = Username
            request.session['Permit_Id'] = "NEW"
            context.update({'Success': "Success"})
        elif Username == "" and pswd == "":
            context.update({})
        else:
            context.update({'Error': "Enter Correct Password and Username"})
    return render(request, "LoginPage/Login.html", context)
  
def Home(request):
    return render(request, 'Home.html', )

def Inpayment(request):
    context = {}
    Username = request.session['Username']
    context.update({
        "UserName": Username,
        'CustomiseReport': CustomiseReport.objects.filter(ReportName="IPT", UserName=Username).exclude(FiledName='id'),
        'ManageUserMail': ManageUser.objects.filter(Status='Active').order_by('MailBoxId').values_list('MailBoxId', flat=True).distinct(),
        'InondeclarationTypeValue': CommonMaster.objects.filter(TypeId=13, StatusId=1),
    })
    return render(request, 'Inpayment/InpaymentList.html', context)

def InpaymentNew(request, arg):
    nowRefId = datetime.now().strftime("%Y%m%d")
    nowJobId = datetime.now().strftime("%Y-%m-%d")
    Username = request.session['Username']
    Permit_Id = request.session['Permit_Id']
    s = SqlDb()
    context = {}
    if arg == "REFUND":
        context.update({
            'REFUND': 'NEW',
            'TypeofRefund': CommonMaster.objects.filter(TypeId=77, StatusId=1).order_by('Name'),
            'ReasonForRefund': CommonMaster.objects.filter(TypeId=76, StatusId=1).order_by('Name')
        })

    if arg == "AMEND":
        context.update({'AMEND': 'AMEND'})

    if arg == "CANCEL":
        context.update({
            'CANCEL': 'CANCEL',
            'CancelType': CommonMaster.objects.filter(TypeId=75, StatusId=1).order_by('Name')
        })

    if arg == 'EDIT' or arg == 'COPY' or arg == 'REFUND' or arg == 'AMEND' or arg == 'CANCEL' or arg == "SHOW":
        for i in InheaderTbl.objects.filter(PermitId=Permit_Id):
            s.cursor.execute(
                'select Top 1 manageuser.LoginStatus,manageuser.DateLastUpdated,manageuser.MailBoxId,manageuser.SeqPool,SequencePool.StartSequence,DeclarantCompany.TradeNetMailboxID,DeclarantCompany.DeclarantName,DeclarantCompany.DeclarantCode,DeclarantCompany.DeclarantTel,DeclarantCompany.CRUEI,DeclarantCompany.Code,DeclarantCompany.name,DeclarantCompany.name1,DeclarantCompany.code from manageuser inner join SequencePool on manageuser.SeqPool=SequencePool.Description inner join DeclarantCompany on DeclarantCompany.TradeNetMailboxID=ManageUser.MailBoxId where ManageUser.UserId='" +'{UserName}'".format(UserName=i.TouchUser))
            headData = s.cursor.fetchall()
            inHeaderPermitId = str(i.PermitId).upper()
            inHeaderMsgId = i.MSGId
            inHeaderJobId = i.JobId
            inHeaderReId = i.Refid
            context.update({
                'EDIT': 'EDIT',
                'Header': InheaderTbl.objects.filter(PermitId=Permit_Id),
            })
        if arg == "SHOW":
            context.update({"SHOW": True})

        if InpaymentRefund.objects.filter(MsgId=i.MSGId).exists():
            context.update({
                'REFUND': 'EDIT',
                'TypeofRefund': CommonMaster.objects.filter(TypeId=77, StatusId=1).order_by('Name'),
                'ReasonForRefund': CommonMaster.objects.filter(TypeId=76, StatusId=1).order_by('Name')
            })
        if InpaymentCancel.objects.filter(MsgId=i.MSGId).exists():
            context.update({
                'CANCEL': 'EDIT',
                'CancelType': CommonMaster.objects.filter(TypeId=75, StatusId=1).order_by('Name')
            })
        if InpaymentAmend.objects.filter(MsgId=i.MSGId).exists():
            context.update({'AMEND': 'AMEND'})

    elif arg == 'NEW':
        s.cursor.execute('select Top 1 manageuser.LoginStatus,manageuser.DateLastUpdated,manageuser.MailBoxId,manageuser.SeqPool,SequencePool.StartSequence,DeclarantCompany.TradeNetMailboxID,DeclarantCompany.DeclarantName,DeclarantCompany.DeclarantCode,DeclarantCompany.DeclarantTel,DeclarantCompany.CRUEI,DeclarantCompany.Code,DeclarantCompany.name,DeclarantCompany.name1,DeclarantCompany.code from manageuser inner join SequencePool on manageuser.SeqPool=SequencePool.Description inner join DeclarantCompany on DeclarantCompany.TradeNetMailboxID=ManageUser.MailBoxId where ManageUser.UserId='" +'{UserName}'".format(
            UserName=request.session['Username']))
        headData = s.cursor.fetchall()
        for i in ManageUser.objects.filter(UserName=Username):
            mailBoxId = i.MailBoxId
            AccountId = i.AccountId
        inHeaderReId = len(InheaderTbl.objects.filter(MSGId__icontains=nowRefId, MessageType="IPTDEC"))+1
        inHeaderReId = ("%03d" % inHeaderReId)
        inHeaderJobId1 = len(PermitCount.objects.filter(TouchTime__icontains=nowJobId, AccountId=AccountId))+1
        inHeaderJobId = f"K{datetime.now().strftime('%y%m%d')}{'%05d' % inHeaderJobId1}" 
        inHeaderMsgId = f"{datetime.now().strftime('%Y%m%d')}{'%04d' % inHeaderJobId1}"
        inHeaderPermitId = f"{Username}{nowRefId}{inHeaderReId}"
        request.session['Permit_Id'] = inHeaderPermitId 

    context.update({
        "UserName": Username, 'PermitId': str(inHeaderPermitId).upper(), 'MsgId': inHeaderMsgId, 'JobId': inHeaderJobId, 'RefId': inHeaderReId, 'headmailId': headData[0][2],
        'headdeclarantName': headData[0][6],
        'headdeclarantCode': headData[0][7],
        'headdeclarantTelephone': headData[0][8],
        'headCrueiNo': headData[0][9],
        'headname': headData[0][11],
        'headname1': headData[0][12],
        'headdataCode': headData[0][13],
        'DeclarationType': CommonMaster.objects.filter(TypeId=1, StatusId=1),
        'InondeclarationTypeValue': CommonMaster.objects.filter(TypeId=13, StatusId=1),
        'CargoType': CommonMaster.objects.filter(TypeId=2, StatusId=1),
        'InwardTransportMode': CommonMaster.objects.filter(TypeId=3, StatusId=1).order_by('Name'),
        'DeclaringFor': CommonMaster.objects.filter(TypeId=80, StatusId=1).order_by('Name'),
        'BgIndicator': CommonMaster.objects.filter(TypeId=4, StatusId=1).order_by('Name'),
        'DocumentAttachmentType': CommonMaster.objects.filter(TypeId=5, StatusId=1).order_by('Name'),
        'totalOuterPack': CommonMaster.objects.filter(TypeId=10, StatusId=1).order_by('Name'),
        'Currency': Currency.objects.all().order_by('Currency'),
        'invoiceTermType': CommonMaster.objects.filter(TypeId=7, StatusId=1).order_by('Name'),
        'Container': CommonMaster.objects.filter(TypeId=6, StatusId=1).order_by('Name'),
        'MakingLot': CommonMaster.objects.filter(TypeId=12, StatusId=1).order_by('Name'),
        'VehicalType': CommonMaster.objects.filter(TypeId=20, StatusId=1).order_by('Name'),
        'EngineCapacity': CommonMaster.objects.filter(TypeId=21, StatusId=1).order_by('Name'),
        'Preferntial': CommonMaster.objects.filter(TypeId=11, StatusId=1).order_by('Name'),
        'ReleaseLocation': ReleaseLocation.objects.all().order_by('locationCode'),
        'ReceiptLocation': ReceiptLocation.objects.all().order_by('locationCode'),
        'LoadingPort': LoadingPort.objects.all().order_by('portcode'),
        'Country': COUNTRY.objects.all().order_by('CountryCode'),
    })
    
    return render(request, 'Inpayment/InpaymentNew.html', context)

def InpaymentHeader(request):
    Username = request.session['Username']
    s = SqlDb()
    for i in ManageUser.objects.filter(UserName=Username):
        mailBoxId = i.MailBoxId
        AccountId = i.AccountId
    nowdata = datetime.now()-timedelta(days=60)
    print("The Data is : ",nowdata.strftime("%Y/%m/%d")) 
    s.cursor.execute("SELECT t1.Id as 'ID', t1.JobId as 'JOB ID', t1.MSGId as 'MSG ID', CONVERT(varchar, t1.TouchTime, 105) AS 'DEC DATE', SUBSTRING(t1.DeclarationType, 1, case when  CHARINDEX(' ', t1.DeclarationType ) = 0 then LEN(t1.DeclarationType) else CHARINDEX(' ', t1.DeclarationType) - 1 end) AS 'DEC TYPE', t1.TouchUser AS 'CREATE', t2.TradeNetMailboxID AS 'DEC ID', CONVERT(varchar, t1.ArrivalDate, 105) AS ETA, t1.PermitNumber AS 'PERMIT NO',t3.Name+' '+t3.Name1 AS 'IMPORTER',STUFF((SELECT distinct(', ' +  US.InHAWBOBL)  FROM ItemDtl US WHERE US.PermitId = t1.PermitId FOR XML PATH('')), 1, 1, '') 'HAWB',CASE  WHEN  t1.InwardTransportMode = '4 : Air' THEN t1.MasterAirwayBill  WHEN t1.InwardTransportMode = '1 : Sea'  THEN t1.OceanBillofLadingNo  ELSE ''  END AS 'MAWB/OBL',t1.LoadingPortCode as POL, t1.MessageType as 'MSG TYPE',t1.InwardTransportMode as TPT, t1.PreviousPermit as 'PRE PMT',t1.GrossReference as 'X REF', t1.InternalRemarks as 'INT REM',SUM(t1.TotalGSTTaxAmt) AS 'GST AMT', t1.Status as 'STATUS', 'Default' as  'COLOR',t1.PermitId  FROM  InHeaderTbl AS t1 left JOIN DeclarantCompany AS t2 ON t1.DeclarantCompanyCode = t2.Code left JOIN Importer AS t3 ON t1.ImporterCompanyCode = t3.Code   left JOIN ManageUser AS t6 ON t6.UserId=t1.TouchUser   where t6.AccountId='" +
                   AccountId + "' and convert(varchar,t1.TouchTime,111)>='"+ nowdata.strftime("%Y/%m/%d")+ " 'GROUP BY t1.Id, t1.JobId, t1.MSGId, t1.TouchTime, t1.TouchUser, t1.DeclarationType, t1.ArrivalDate, t1.PermitId, t1.InwardTransportMode, t1.MasterAirwayBill, t1.OceanBillofLadingNo, t1.LoadingPortCode, t1.MessageType, t1.InwardTransportMode, t1.PreviousPermit,t1.InternalRemarks, t1.Status, t2.TradeNetMailboxID,t2.DeclarantName,t1.GrossReference ,t1.License,t1.ReleaseLocation,t1.RecepitLocation,t1.DeclarningFor,t3.Name,t3.Name1,t6.AccountId,t1.PermitNumber")
    
    #result = (pd.DataFrame(list(s.cursor.fetchall()), columns=["id","JobId","MSGId","DECDATE","DECTYPE","CREATE","DECID","ETA","PERMITNO","IMPORTER","HAWB","MAWBOBL","POL","MSGTYPE","TPT","PREPMT","XREF","INTREM","GSTAMT","STATUS","default","PermitId"])).to_dict('records')
    headLen = list(s.cursor.fetchall())
    headLen.sort(reverse=True) 
    result = []
    result = list(map(lambda row: {'id': row[0], 'JobId': row[1], 'MSGId': row[2], 'DECDATE': row[3], 'DECTYPE': row[4],
                                   'CREATE': row[5], 'DECID': row[6], 'ETA': row[7], 'PERMITNO': row[8],
                                   'IMPORTER': row[9], 'HAWB': row[10], 'MAWBOBL': row[11], 'POL': row[12],
                                   'MSGTYPE': row[13], 'TPT': row[14], 'PREPMT': row[15], 'XREF': row[16],
                                   'INTREM': row[17], 'GSTAMT': str(row[18]), 'STATUS': row[19], 'default': row[20],
                                   'PermitId': row[21]}, headLen))
    return JsonResponse(result, safe=False)

def ItemExcelDownload(request):
    response = HttpResponse(open('D:\\New folder\\NNR REPORT FILE\\OUT & COO Type Changes\\RET\\RET\\ExcelTemplate\\InPaymentExcel.xlsx', 'rb').read())
    response['Content-Type'] = 'text/csv'
    response['Content-Disposition'] = f'attachment; filename=InPaymentExcel.xlsx'
    return response

def ItemExcelUpload(request):
    xlsx_file = request.FILES['file']
    PermitId = request.POST.get('PermitId')
    MsgType = request.POST.get('MsgType')
    userName = request.POST.get('UserName')
    TouchTime = request.POST.get('TouchTime')

    ItemInfo = pd.read_excel(xlsx_file, sheet_name="ItemInfo")
    CascInfo = pd.read_excel(xlsx_file, sheet_name="Casccodes")
    ContainerInfo = pd.read_excel(xlsx_file, sheet_name="ContainerInfo")
    ItemData = []
    CascData = []
    ContainerData = []

    ItemColumns = {
        'CountryofOrigin': '',
        'HSCode': '',
        'HSQty': '0.00',
        'TotalLineAmount': '0.00',
        'ItemCode': '',
        'Description': '',
        'DGIndicator': 'False',
        'Brand': '',
        'Model': '',
        'InHAWBOBL': '',
        'OutHAWBOBL': '',
        'HSUOM': '--SELECT--',
        'InvoiceNumber': '',
        'ItemCurrency': '--SELECT--',
        'UnitPrice': '0.00',
        'TotalDutiableQty': '0.00',
        'TotalDutiableUOM': '--SELECT--',
        'DutiableQty': '0.00',
        'DutiableUOM': '--SELECT--',
        'OuterPackQty': '0.00',
        'OuterPackUOM': '--SELECT--',
        'InPackQty': '0.00',
        'InPackUOM': '--SELECT--',
        'InnerPackQty': '0.00',
        'InnerPackUOM': '--SELECT--',
        'InmostPackQty': '0.00',
        'InmostPackUOM': '--SELECT--',
        'LastSellingPrice': '0.00',
        'TarrifPreferentialCode': '--SELECT--',
        'OtherTaxRate': '0.00',
        'OtherTaxUOM': '--SELECT--',
        'OtherTaxAmount': '0.00',
        'CurrentLot': '',
        'PreviousLot': '',
        'AlcoholPercentage': '0.00',
        'ShippingMarks1': '',
        'ShippingMarks2': '',
        'ShippingMarks3': '',
        'ShippingMarks4': '',
    }

    CascColumn = {
        'ItemNo': '',
        'ProductCode': '',
        'Quantity': '0.00',
        'ProductUOM': '--SELECT--',
        'RowNo': '',
        'CascCode1': '',
        'CascCode2': '',
        'CascCode3': '',
        'CASCId': '',
    }

    ContainerColumn = {
        'SNo': '',
        'ContainerNo': '',
        'SizeType': '',
        'Weight': '',
        'SealNo': '',
    }

    ItemInfo.fillna(ItemColumns, inplace=True)
    CascInfo.fillna(CascColumn, inplace=True)
    ContainerInfo.fillna(ContainerColumn, inplace=True)

    for index, row in ItemInfo.iterrows():
        ItemLen = len(ItemDtl.objects.filter(PermitId=PermitId))+(index+1)
        try:
            ItemData.append(ItemDtl(
                Contry=row['CountryofOrigin'],
                HSCode=row['HSCode'],
                HSQty=row['HSQty'],
                TotalLineAmount=row['TotalLineAmount'],
                Description=row['Description'],
                DGIndicator=row['DGIndicator'],
                Brand=row['Brand'],
                Model=row['Model'],
                InHAWBOBL=row['InHAWBOBL'],
                HSUOM=row['HSUOM'],
                InvoiceNo=row['InvoiceNumber'],
                UnitPriceCurrency=row['ItemCurrency'],
                UnitPrice=row['UnitPrice'],
                TotalDutiableQty=row['TotalDutiableQty'],
                TotalDutiableUOM=row['TotalDutiableUOM'],
                DutiableQty=row['DutiableQty'],
                DutiableUOM=row['DutiableUOM'],
                OPQty=row['OuterPackQty'],
                OPUOM=row['OuterPackUOM'],
                IPQty=row['InPackQty'],
                IPUOM=row['InPackUOM'],
                InPqty=row['InnerPackQty'],
                InPUOM=row['InnerPackUOM'],
                ImPQty=row['InmostPackQty'],
                ImPUOM=row['InmostPackUOM'],
                LSPValue=row['LastSellingPrice'],
                PreferentialCode=row['TarrifPreferentialCode'],
                OtherTaxRate=row['OtherTaxRate'],
                OtherTaxUOM=row['OtherTaxUOM'],
                OtherTaxAmount=row['OtherTaxAmount'],
                CurrentLot=row['CurrentLot'],
                PreviousLot=row['PreviousLot'],
                AlcoholPer=row['AlcoholPercentage'],
                ShippingMarks1=row['ShippingMarks1'],
                ShippingMarks2=row['ShippingMarks2'],
                ShippingMarks3=row['ShippingMarks3'],
                ShippingMarks4=row['ShippingMarks4'],
                ItemNo=ItemLen,
                PermitId=PermitId,
                MessageType=MsgType,
                TouchUser=userName,
                TouchTime=TouchTime,
                InvoiceQuantity="0.00",
                ChkUnitPrice='0.00',
                ExchangeRate='0.00',
                SumExchangeRate='0.00',
                InvoiceCharges='0.00',
                CIFFOB='0.00',
                GSTRate='0.00',
                GSTUOM='PER',
                GSTAmount='0.00',
                ExciseDutyRate='0.00',
                ExciseDutyUOM='',
                ExciseDutyAmount='0.00',
                CustomsDutyRate='0.00',
                CustomsDutyUOM='',
                CustomsDutyAmount='0.00',
                Making='--SELECT--',
                VehicleType='--SELECT--',
                EngineCapcity="--SELECT--",
                EngineCapUOM='--SELECT--',
                orignaldatereg=TouchTime,
                OptionalChrgeUOM='--SELECT--',
                Optioncahrge='0.00',
                OptionalSumtotal='0.00',
                OptionalSumExchage='0.00'
            ))
        except Exception as e:
            print("the Errro is: " + str(e))

    for index, row in CascInfo.iterrows():
        if row['ProductCode'] != "":
            CascData.append(Cascdtl(ItemNo=row['ItemNo'],
                                    ProductCode=row['ProductCode'],
                                    Quantity=row['Quantity'],
                                    ProductUOM=row['ProductUOM'],
                                    RowNo=row['RowNo'],
                                    CascCode1=row['CascCode1'],
                                    CascCode2=row['CascCode2'],
                                    CascCode3=row['CascCode3'],
                                    PermitId=PermitId,
                                    MessageType=MsgType,
                                    TouchUser=userName,
                                    TouchTime=TouchTime,
                                    CascId=row['CASCId']))

    for index, row in ContainerInfo.iterrows():
        if row['SNo'] != "":
            ContainerData.append(
                PermitId=PermitId,
                RowNo=row['SNo'],
                ContainerNo=row['ContainerNo'],
                size=row['SizeType'],
                weight=row['Weight'],
                SealNo=row['SealNo'],
                MessageType=MsgType,
                TouchUser=userName,
                TouchTime=TouchTime,
            )

    ItemDtl.objects.bulk_create(ItemData)
    Cascdtl.objects.bulk_create(CascData)
    ContainerDtl.objects.bulk_create(ContainerData)
    Item = list(ItemDtl.objects.filter(PermitId=PermitId).order_by('ItemNo').values())
    ItemCasc = list(Cascdtl.objects.filter(PermitId=PermitId).order_by('ItemNo').values())

    return JsonResponse({'Item': Item, 'ItemCasc': ItemCasc, "Result": "Deleted"})

def AllItemUpdate(request):
    Item = json.loads(request.POST.get('Item'))
    PermitId = request.POST.get('PermitId')
    df = pd.DataFrame(Item)
    s = SqlDb()
    for _, rows in df.iterrows():
        Qry = f"UPDATE ItemDtl SET MessageType  = %s  , HSCode  = %s  , Description  = %s  , DGIndicator  = %s  , Contry  = %s  , Brand  = %s  , Model  = %s  , InHAWBOBL  = %s  , DutiableQty  = %s  , DutiableUOM  = %s  , TotalDutiableQty  = %s  , TotalDutiableUOM  = %s  , InvoiceQuantity  = %s  , HSQty  = %s  , HSUOM  = %s  , AlcoholPer  = %s  , InvoiceNo  = %s  , ChkUnitPrice  = %s  , UnitPrice  = %s  , UnitPriceCurrency  = %s  , ExchangeRate  = %s  , SumExchangeRate  = %s  , TotalLineAmount  = %s  , InvoiceCharges  = %s  , CIFFOB  = %s  , OPQty  = %s  , OPUOM  = %s  , IPQty  = %s  , IPUOM  = %s  , InPqty  = %s  , InPUOM  = %s  , ImPQty  = %s  , ImPUOM  = %s  , PreferentialCode  = %s  , GSTRate  = %s  , GSTUOM  = %s  , GSTAmount  = %s  , ExciseDutyRate  = %s  , ExciseDutyUOM  = %s  , ExciseDutyAmount  = %s  , CustomsDutyRate  = %s  , CustomsDutyUOM  = %s  , CustomsDutyAmount  = %s  , OtherTaxRate  = %s  , OtherTaxUOM  = %s  , OtherTaxAmount  = %s  , CurrentLot  = %s  , PreviousLot  = %s  , LSPValue  = %s  , Making  = %s  , ShippingMarks1  = %s  , ShippingMarks2  = %s  , ShippingMarks3  = %s  , ShippingMarks4  = %s  , TouchUser  = %s  , TouchTime  = %s  , VehicleType  = %s  , EngineCapcity  = %s  , EngineCapUOM  = %s  , orignaldatereg  = %s  , OptionalChrgeUOM  = %s  , Optioncahrge  = %s  , OptionalSumtotal  = %s  , OptionalSumExchage  = %s  WHERE ItemNo  = %s AND PermitId  = %s"
        Val = (rows['MessageType'], rows['HSCode'], rows['Description'], rows['DGIndicator'], rows['Contry'], rows['Brand'], rows['Model'], rows['InHAWBOBL'], rows['DutiableQty'], rows['DutiableUOM'], rows['TotalDutiableQty'], rows['TotalDutiableUOM'], rows['InvoiceQuantity'], rows['HSQty'], rows['HSUOM'], rows['AlcoholPer'], rows['InvoiceNo'], rows['ChkUnitPrice'], rows['UnitPrice'], rows['UnitPriceCurrency'], rows['ExchangeRate'], rows['SumExchangeRate'], rows['TotalLineAmount'], rows['InvoiceCharges'], rows['CIFFOB'], rows['OPQty'], rows['OPUOM'], rows['IPQty'], rows['IPUOM'], rows['InPqty'], rows['InPUOM'], rows['ImPQty'], rows['ImPUOM'], rows['PreferentialCode'], rows['GSTRate'],
               rows['GSTUOM'], rows['GSTAmount'], rows['ExciseDutyRate'], rows['ExciseDutyUOM'], rows['ExciseDutyAmount'], rows['CustomsDutyRate'], rows['CustomsDutyUOM'], rows['CustomsDutyAmount'], rows['OtherTaxRate'], rows['OtherTaxUOM'], rows['OtherTaxAmount'], rows['CurrentLot'], rows['PreviousLot'], rows['LSPValue'], rows['Making'], rows['ShippingMarks1'], rows['ShippingMarks2'], rows['ShippingMarks3'], rows['ShippingMarks4'], rows['TouchUser'], rows['TouchTime'], rows['VehicleType'], rows['EngineCapcity'], rows['EngineCapUOM'], rows['orignaldatereg'], rows['OptionalChrgeUOM'], rows['Optioncahrge'], rows['OptionalSumtotal'], rows['OptionalSumExchage'], rows['ItemNo'], rows['PermitId'])
        s.cursor.execute(Qry, Val)
    s.conn.commit()
    Item = list(ItemDtl.objects.filter(
        PermitId=PermitId).order_by('ItemNo').values())
    ItemCasc = list(Cascdtl.objects.filter( 
        PermitId=PermitId).order_by('ItemNo').values())
    return JsonResponse({'Item': Item, 'ItemCasc': ItemCasc, "Result": "updated"})

def ItemConsolidate(request):
    permitId = request.POST.get('PermitId')

    results = (ItemDtl.objects.filter(PermitId=permitId).values('HSCode', 'Description', 'Contry', 'UnitPriceCurrency').annotate(ItemNo=Min('ItemNo'),
                         DutiableQty=Sum('DutiableQty'),
                         TotalDutiableQty=Sum('TotalDutiableQty'),
                         InvoiceQuantity=Sum('InvoiceQuantity'),
                         HSQty=Sum('HSQty'),
                         AlcoholPer=Sum('AlcoholPer'),
                         UnitPrice=Sum('UnitPrice'),
                         SumExchangeRate=Sum('SumExchangeRate'),
                         TotalLineAmount=Sum('TotalLineAmount'),
                         InvoiceCharges=Sum('InvoiceCharges'),
                         CIFFOB=Sum('CIFFOB'),
                         OPQty=Sum('OPQty'),
                         IPQty=Sum('IPQty'),
                         InPqty=Sum('InPqty'),
                         ImPQty=Sum('ImPQty'),
                         GSTAmount=Sum('GSTAmount'),
                         ExciseDutyAmount=Sum('ExciseDutyAmount'),
                         CustomsDutyAmount=Sum('CustomsDutyAmount'),
                         OtherTaxAmount=Sum('OtherTaxAmount'),
                         OptionalSumtotal=Sum('OptionalSumtotal'),
                         ).order_by('ItemNo'))
    itemNum = []
    for p in results:
        itemNum.append(p['ItemNo'])
        ItemDtl.objects.filter(PermitId=permitId, ItemNo=p['ItemNo']).update(
            DutiableQty=p['DutiableQty'],
            TotalDutiableQty=p['TotalDutiableQty'],
            InvoiceQuantity=p['InvoiceQuantity'],
            HSQty=p['HSQty'],
            AlcoholPer=p['AlcoholPer'],
            UnitPrice=p['UnitPrice'],
            SumExchangeRate=p['SumExchangeRate'],
            TotalLineAmount=p['TotalLineAmount'],
            InvoiceCharges=p['InvoiceCharges'],
            CIFFOB=p['CIFFOB'],
            OPQty=p['OPQty'],
            IPQty=p['IPQty'],
            InPqty=p['InPqty'],
            ImPQty=p['ImPQty'],
            GSTAmount=p['GSTAmount'],
            ExciseDutyAmount=p['ExciseDutyAmount'],
            CustomsDutyAmount=p['CustomsDutyAmount'],
            OtherTaxAmount=p['OtherTaxAmount'],
            OptionalSumtotal=p['OptionalSumtotal']
        )

    for j in ItemDtl.objects.filter(PermitId=permitId):
        if j.ItemNo not in itemNum:
            ItemDtl.objects.filter(PermitId=permitId, ItemNo=j.ItemNo).delete()
            Cascdtl.objects.filter(PermitId=permitId, ItemNo=j.ItemNo).delete()
    c = 1
    for p in itemNum:
        ItemDtl.objects.filter(PermitId=permitId, ItemNo=p).update(ItemNo=c)
        Cascdtl.objects.filter(PermitId=permitId, ItemNo=p).update(ItemNo=c)
        c = c+1

    Item = list(ItemDtl.objects.filter(PermitId=permitId).order_by('ItemNo').values())
    ItemCasc = list(Cascdtl.objects.filter(PermitId=permitId).order_by('ItemNo').values())
    return JsonResponse({'Item': Item, 'ItemCasc': ItemCasc, "Result": "updated"})

def EditInpayment(request):
    request.session['Permit_Id'] = request.POST.get('Permitid')
    return JsonResponse({"Checking Values  ": 'true'})

def RefundLoad(request):
    return JsonResponse({
        "Refund": list(InpaymentRefund.objects.filter(MsgId=request.POST.get('MsgId')).values()),
        'RefundValSummary': list(RefundValSummary.objects.filter(MsgId=request.POST.get('MsgId')).values()),
        'ReundItemSumm': list(ReundItemSumm.objects.filter(MsgId=request.POST.get('MsgId')).values()),
    })

def CanceLoad(request):
    return JsonResponse({
        "Cancel": list(InpaymentCancel.objects.filter(MsgId=request.POST.get('MsgId')).values())
    })

def AmendLoad(request):
    return JsonResponse({
        "Amend": list(InpaymentAmend.objects.filter(MsgId=request.POST.get('MsgId')).values())
    })

def DeleteAllFunction(request): 
    data = json.loads(request.POST.get('my_data'))
    for d in data:
        obj = InheaderTbl.objects.get(PermitId=d)
        obj.Status = "DEL"
        obj.save()
    return JsonResponse({'Deleted': "Deleted"}) 

def LoadingPartyModels(request):
    return JsonResponse({
        "Importer": list(Importer.objects.filter(status='Active').order_by('name').values())
    })

def InpaymentItemDelHblHawb(request):
    for item in ItemDtl.objects.filter(PermitId=request.session['Permit_Id']):
        obj = ItemDtl.objects.get(id=item.id)
        obj.InHAWBOBL = ""
        obj.save()
    return JsonResponse({
        'Item': list(ItemDtl.objects.filter(PermitId=request.session['Permit_Id']).order_by('ItemNo').values())
    })

class CargoPageSave(View,SqlDb):
    
    def dispatch(self, request):
        SqlDb.__init__(self)
        DbName = request.POST.get('ModelName')
        if DbName == 'ImporterModel':
            Qry = "select code from Importer where code = %s"
            val = (request.POST.get('code'),)
            self.cursor.execute(Qry,val)

            if not(self.cursor.fetchall()):

                Qry = "INSERT INTO Importer(code,cruei,name,name1,status,TouchUser,TouchTime) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                val = (request.POST.get('code'),request.POST.get('cruei'),request.POST.get('name'),request.POST.get('name1'),'Active',request.POST.get('TouchUser'),request.POST.get('TouchTime'))
                self.cursor.execute(Qry,val)
                self.conn.commit()
                self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM Importer WHERE status = 'Active' ")
                importer = self.cursor.fetchall()

                return JsonResponse({"Result": "Importer Saved ...!","Importer" : (pd.DataFrame(list(importer), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records')})
            else:
                return JsonResponse({"Result": "Importer Code Already Exists ...!"})
        
        elif DbName == 'InawrdModel':
            Qry = "select code from InwardCarrierAgent where code = %s"
            val = (request.POST.get('code'),)
            self.cursor.execute(Qry,val)
            if not(self.cursor.fetchall()):
                Qry = "INSERT INTO InwardCarrierAgent(code,cruei,name,name1,status,TouchUser,TouchTime) VALUES (%s,%s,%s,%s,%s,%s,%s) "
                Val = (request.POST.get('code'),request.POST.get('cruei'),request.POST.get('name'),request.POST.get('name1'),'Active',request.POST.get('TouchUser'),request.POST.get('TouchTime'))
                self.cursor.execute(Qry,Val)
                self.conn.commit()

                self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM InwardCarrierAgent WHERE status = 'Active' ")
                return JsonResponse({"Result": "InwardCarrierAgent Saved ...!","Inward" : (pd.DataFrame(list(self.cursor.fetchall()), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records')})
            else:
                return JsonResponse({"Result": "InwardCarrierAgent Code Already Exists ...!"})
            
        elif DbName == 'FreightModel':
            Qry = "select code from FreightForwarder where code = %s"
            Val = (request.POST.get('code'),)
            self.cursor.execute(Qry,Val)
            if not(self.cursor.fetchall()):
                Qry = "INSERT INTO FreightForwarder(code,cruei,name,name1,status,TouchUser,TouchTime) VALUES (%s,%s,%s,%s,%s,%s,%s) "
                Val = (request.POST.get('code'),request.POST.get('cruei'),request.POST.get('name'),request.POST.get('name1'),'Active',request.POST.get('TouchUser'),request.POST.get('TouchTime'))
                self.cursor.execute(Qry,Val)
                self.conn.commit()
                self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM FreightForwarder WHERE status = 'Active' ")
                fright = self.cursor.fetchall()
                return JsonResponse({"Result": "FreightForwarder Saved ...!","Frieght" : (pd.DataFrame(list(fright), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),})
            else:
                return JsonResponse({"Result": "FreightForwarder Code Already Exists ...!"})
            
        elif DbName == 'ClaimantModel':
            Qry = "select ClaimantCode from ClaimantParty  where ClaimantCode = %s"
            Val = (request.POST.get('ClaimantCode'),)
            self.cursor.execute(Qry,Val)
            if not(self.cursor.fetchall()):
                Qry = "INSERT INTO ClaimantParty (ClaimantCode,cruei,name,name1,ClaimantName,ClaimantName1,status,TouchUser,TouchTime) VALUES  (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                Val = (request.POST.get('ClaimantCode'),request.POST.get('cruei'),request.POST.get('name'),request.POST.get('name1'),request.POST.get('ClaimantName'),request.POST.get('ClaimantName1'),'Active',request.POST.get('TouchUser'),request.POST.get('TouchTime'))
                self.cursor.execute(Qry,Val)
                self.conn.commit()
                return JsonResponse({"Result": "ClaimantParty  Saved ...!"})
            else:
                return JsonResponse({"Result": "ClaimantParty  Code Already Exists ...!"})
            
        elif DbName == 'SupplierModel':
            Qry = "select code from SUPPLIERMANUFACTURERPARTY  where code = %s"
            Val = (request.POST.get('code'),)
            self.cursor.execute(Qry,Val)
            if not(self.cursor.fetchall()):
                Qry = "INSERT INTO SUPPLIERMANUFACTURERPARTY (code,cruei,name,name1,status,TouchUser,TouchTime) VALUES  (%s,%s,%s,%s,%s,%s,%s)"
                Val = (request.POST.get('code'),request.POST.get('cruei'),request.POST.get('name'),request.POST.get('name1'),'Active',request.POST.get('TouchUser'),request.POST.get('TouchTime'))
                self.cursor.execute(Qry,Val)
                self.conn.commit()
                self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM SUPPLIERMANUFACTURERPARTY WHERE status = 'Active' ")
                supply = self.cursor.fetchall()
                return JsonResponse({"Result": "SUPPLIERMANUFACTURERPARTY  Saved ...!","Supply" : (pd.DataFrame(list(supply), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),})
            else:
                return JsonResponse({"Result": "SUPPLIERMANUFACTURERPARTY  Code Already Exists ...!"})
            
        elif DbName == 'InhouseItemCodeModel':
            Qry = "select code from InhouseItemCode where code = %s"
            Val = (request.POST.get('code'),)
            self.cursor.execute(Qry,Val)
            if not(self.cursor.fetchall()):
                Qry = "INSERT INTO InhouseItemCode(InhouseCode,Hscode,Description,Brand,Model,DgIndicator,DeclType,ProductCode,TouchUser,TouchTime) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                Val = (request.POST.get('InhouseCode'),request.POST.get('Hscode'),request.POST.get('Description'),request.POST.get('Brand'),request.POST.get('Model'),request.POST.get('DgIndicator'),request.POST.get('DeclType'),request.POST.get('ProductCode'),request.POST.get('TouchUser'),request.POST.get('TouchTime'))
                self.cursor.execute(Qry,Val)
                self.conn.commit()
                return JsonResponse({"Result": "InhouseItemCode Saved ...!"})
            else:
                return JsonResponse({"Result": "InhouseItemCode Code Already Exists ...!"})
        
        elif DbName == 'GET':
            self.cursor.execute("SELECT * FROM Importer WHERE status = 'Active' ")
            return JsonResponse({"Importer" : self.cursor.fetchall()})
        else:
            return JsonResponse({"error": "Invalid function name"}, status=404)
    def get(self):
        self.cursor.execute("SELECT * FROM Importer WHERE status = 'Active' ")
        return JsonResponse({"Importer" : self.cursor.fetchall()})

class ContainerSave(View,SqlDb):
    
    def post(self, request):
        SqlDb.__init__(self)
        if request.POST.get('Method') == "SAVE":
            self.cursor.execute(f"select RowNo , PermitId from ContainerDtl where RowNo = '{request.POST.get('RowNo')}' AND PermitId = '{request.POST.get('PermitId')}'")
            result = self.cursor.fetchall()
            if not(result):
                self.cursor.execute(f"INSERT INTO ContainerDtl (PermitId, RowNo,ContainerNo, size, weight,SealNo, MessageType,TouchUser,TouchTime) VALUES ('{request.POST.get('PermitId')}','{request.POST.get('RowNo')}','{request.POST.get('ContainerNo')}','{request.POST.get('size')}','{request.POST.get('weight')}','{request.POST.get('SealNo')}','{request.POST.get('MessageType')}','{request.POST.get('TouchUser')}','{request.POST.get('TouchTime')}')")
                self.conn.commit()
                self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.POST.get('PermitId')}' Order By RowNo ")
                return JsonResponse({"ContainerValue": list(self.cursor.fetchall()),'Result':"Container Data Saved SuccessFully ...!"})
            else:
                self.cursor.execute(f"Update ContainerDtl set ContainerNo = '{request.POST.get('ContainerNo')}',size = '{request.POST.get('size')}',weight =  '{request.POST.get('weight')}',SealNo = '{request.POST.get('SealNo')}',MessageType = '{request.POST.get('MessageType')}',TouchUser = '{request.POST.get('TouchUser')}',TouchTime = '{request.POST.get('TouchTime')}' where RowNo = '{request.POST.get('RowNo')}' AND PermitId = '{request.POST.get('PermitId')}'")
                self.conn.commit()

                self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.POST.get('PermitId')}' Order By RowNo")
                return JsonResponse({"ContainerValue": list(self.cursor.fetchall()),'Result':"Container Updated SuccessFully ...!"})
            
        elif request.POST.get('Method') == "DELETE":

            self.cursor.execute(f"DELETE FROM ContainerDtl where PermitId = '{request.POST.get('PermitId')}' AND RowNo = '{request.POST.get('SNo')}' ")
            self.conn.commit()

            self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.POST.get('PermitId')}' Order By RowNo ")
            c = 1
            for j in self.cursor.fetchall():
                self.cursor.execute(f"UPDATE ContainerDtl SET RowNo = {c} WHERE PermitId = '{j[1]}' AND RowNo = '{j[2]}'")
                c += 1
            self.conn.commit()

            self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.POST.get('PermitId')}' Order By RowNo ")
            return JsonResponse({"ContainerValue": list(self.cursor.fetchall()),'Result':"Deleted SuccessFully ...!"})
        
        elif request.POST.get('Method') == "CHECKDELETE":

            for ids in json.loads(request.POST.get('IDS')):
                self.cursor.execute(f"DELETE FROM ContainerDtl where id = {ids}")
            self.conn.commit()

            self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.POST.get('PermitId')}' Order By RowNo ")
            c = 1
            for j in self.cursor.fetchall():
                self.cursor.execute(f"UPDATE ContainerDtl SET RowNo = {c} WHERE PermitId = '{j[1]}' AND RowNo = '{j[2]}'")
                c += 1
            self.conn.commit()

            self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.POST.get('PermitId')}' Order By RowNo ")
            return JsonResponse({"ContainerValue": list(self.cursor.fetchall()),'Result':"Deleted SuccessFully ...!"})
        
        elif request.POST.get('Method') == "LOAD":
            self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.POST.get('PermitId')}' Order By RowNo ")
            return JsonResponse({"ContainerValue": list(self.cursor.fetchall()),'Result':"Deleted SuccessFully ...!"})
        
    def get(self,request):
        self.cursor.execute(f"select * from ContainerDtl where PermitId = '{request.GET.get('PermitId')}' Order By RowNo")
        return JsonResponse({"ContainerValue": list(self.cursor.fetchall())})
    
class PartyPage(View,SqlDb):
    def get(self,request):
        SqlDb.__init__(self)
        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM Importer WHERE status = 'Active' ORDER BY Code")
        importer = self.cursor.fetchall()

        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM InwardCarrierAgent WHERE status = 'Active' ORDER BY Code")
        inward = self.cursor.fetchall()

        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM FreightForwarder WHERE status = 'Active' ORDER BY Code")
        fright = self.cursor.fetchall()

        self.cursor.execute("SELECT Name,Name1,CRUEI,ClaimantName,ClaimantName1,ClaimantCode,Name2 FROM ClaimantParty WHERE status = 'Active' ")
        claimant = self.cursor.fetchall() 

        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM SUPPLIERMANUFACTURERPARTY WHERE status = 'Active' ORDER BY Code")
        supply = self.cursor.fetchall()

        self.cursor.execute("SELECT InhouseCode,HSCode,Description,Brand,Model,DGIndicator,DeclType,ProductCode FROM InhouseItemCode")
        inhouse = self.cursor.fetchall()

        self.cursor.execute("SELECT Id,Sno,Name,ContentType,Data,DocumentType,InPaymentId,FilePath,Size,PermitId,Type FROM InFile WHERE PermitId = '{}' ".format(request.session['Permit_Id']))
        inFile = self.cursor.fetchall()


        return JsonResponse(
            {
                'Infile': (pd.DataFrame(list(inFile), columns=["Id","Sno","Name","ContentType","Data","DocumentType","InPaymentId","FilePath","Size","PermitId","Type"])).to_dict('records'),
                "Importer" : (pd.DataFrame(list(importer), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),
                "Inward" : (pd.DataFrame(list(inward), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),
                "Frieght" : (pd.DataFrame(list(fright), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),
                "Claimant" : (pd.DataFrame(list(claimant), columns=["Name","Name1","CRUEI","ClaimantName","ClaimantName1","ClaimantCode","Name2"])).to_dict('records'),
                "Supply" : (pd.DataFrame(list(supply), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),
                "Inhouse" : (pd.DataFrame(list(inhouse), columns=["InhouseCode","HSCode","Description","Brand","Model","DGIndicator","DeclType","ProductCode"])).to_dict('records'),
            }
        )
    
class CpcLoadClass(View,SqlDb):
    def get(self,request):
        SqlDb.__init__(self)

        self.cursor.execute("SELECT PermitId,MessageType,RowNo,CpcType,ProcessingCode1,ProcessingCode2,ProcessingCode3 FROM CpcDtl WHERE PermitId = '{}' AND CpcType = 'AEO' ".format(request.session['Permit_Id']))
        CpAeo = self.cursor.fetchall()

        self.cursor.execute("SELECT PermitId,MessageType,RowNo,CpcType,ProcessingCode1,ProcessingCode2,ProcessingCode3 FROM CpcDtl WHERE PermitId = '{}' AND CpcType = 'CWC' ".format(request.session['Permit_Id']))
        CpCwc = self.cursor.fetchall()

        self.cursor.execute("SELECT PermitId,MessageType,RowNo,CpcType,ProcessingCode1,ProcessingCode2,ProcessingCode3 FROM CpcDtl WHERE PermitId = '{}' AND CpcType = 'SCHEME' ".format(request.session['Permit_Id']))
        CpScheme = self.cursor.fetchall()


        return JsonResponse(
            {
                'CpAeo': (pd.DataFrame(list(CpAeo), columns=["PermitId","MessageType","RowNo","CpcType","ProcessingCode1","ProcessingCode2","ProcessingCode3"])).to_dict('records'),
                'CpCwc': (pd.DataFrame(list(CpCwc), columns=["PermitId","MessageType","RowNo","CpcType","ProcessingCode1","ProcessingCode2","ProcessingCode3"])).to_dict('records'),
                'CpScheme': (pd.DataFrame(list(CpScheme), columns=["PermitId","MessageType","RowNo","CpcType","ProcessingCode1","ProcessingCode2","ProcessingCode3"])).to_dict('records'),
            }
        )

def headAttachDownloadFunction(request, ID):
    data = InFile.objects.filter(id=ID)
    for i in data:
        FilePath = i.FilePath
        FileName = i.Name
        FileType = i.ContentType
    response = HttpResponse(open(FilePath+FileName, 'rb').read())
    response['Content-Type'] = FileType
    response['Content-Disposition'] = f'attachment; filename={str(FileName)}'
    return response

def ContainerDel(request,arg):
    ContainerDtl.objects.get(id = arg).delete()
    return JsonResponse({"Deleted": "Delete"})

class CascProductCodesViewSets(viewsets.ModelViewSet):
    serializer_class = CascProductCodesSerializer
    queryset = CascProductCodes.objects.all()
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_fields = ["HSCode","Description","CASCCode"]
    search_fields = ["HSCode","Description","CASCCode"]
    ordering_fields = "__all__"
    ordering = ['HSCode']

class HsCodeCodesViewSets(viewsets.ModelViewSet):
    serializer_class = HsCodesSerializer
    queryset = HsCode.objects.all()
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    filterset_fields = ["HSCode","Description"]
    search_fields = ["HSCode","Description"]
    ordering_fields = "__all__"
    ordering = ['HSCode']
  
class InvoiceInpayment(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)

    def get(self,request,PermitId):
        self.cursor.execute(f"select * from InvoiceDtl WHERE PermitId = '{PermitId}' ORDER BY SNo")
        headers = [i[0] for i in self.cursor.description]
        return JsonResponse({"invoice" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')})
    
class ItemInpayment(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)

    def get(self,request,PermitId):
        cotext = {}
        self.cursor.execute(f"select * from ItemDtl WHERE PermitId = '{PermitId}' ORDER BY ItemNo")
        headers = [i[0] for i in self.cursor.description]
        cotext.update({
            "item" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')
        })
        self.cursor.execute(f"select * from Cascdtl WHERE PermitId = '{PermitId}' ORDER BY ItemNo")
        headers = [i[0] for i in self.cursor.description]
        cotext.update({
            "itemCasc" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')
        })
        return JsonResponse(cotext)

class InPaymentItemLoad(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)

        self.cursor.execute("SELECT InhouseCode,HSCode,Description,Brand,Model,DGIndicator,DeclType,Productcode FROM InhouseItemCode WHERE DeclType = 'INPAYMENT' ")
        self.inhouseItemCode = self.cursor.fetchall()

        self.cursor.execute("SELECT HSCode,Description,UOM,Typeid,DUTYTYPID,Inpayment,InnonPayment,Out,Co,Transhipment,RPNEXPORT,DuitableUom,Excisedutyuom,Excisedutyrate,Customsdutyuom,Customsdutyrate,Kgmvisible FROM HSCode")#ImpControll,OutControll,TransControll <---This Field Add Only Kaizen Portal 
        self.hsCode = self.cursor.fetchall()

        self.cursor.execute("SELECT HSCode FROM ChkHsCode ")
        self.chkHsCode = self.cursor.fetchall()

    def get(self,request):
        return JsonResponse({
            "inhouseItemCode" : (pd.DataFrame(list(self.inhouseItemCode), columns=["InhouseCode", "HSCode", "Description","Brand","Model", "DGIndicator", "DeclType","Productcode"])).to_dict('records'),
            "hsCode" : (pd.DataFrame(list(self.hsCode), columns=['HSCode','Description','UOM','Typeid','DUTYTYPID','Inpayment','InnonPayment','Out','Co','Transhipment','RPNEXPORT','DuitableUom','Excisedutyuom','Excisedutyrate','Customsdutyuom','Customsdutyrate','Kgmvisible'])).to_dict('records'),#,'ImpControll ,'OutControll','TransControll'<---This Field Add Only Kaizen Portal  '
            "chkHsCode" : (pd.DataFrame(list(self.chkHsCode), columns=["HSCode"])).to_dict('records'),
        })