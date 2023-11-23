from django.shortcuts import render
from KttApp.views import SqlDb
from django.views import View
from datetime import * 
import pandas as pd
from KttApp.models import *
from django.http import JsonResponse
import json

def OutList(request):
    context = {}
    Username = request.session['Username']
    context.update({"UserName":Username})
    return render(request , 'Out/OutList.html',context)

class outListTable(View,SqlDb):
    def __init__(self): 
        SqlDb.__init__(self)
       
    def get(self,request):
        Username = request.session['Username'] 

        self.cursor.execute("SELECT AccountId FROM ManageUser WHERE UserName = '{}' ".format(Username))
        AccountId = self.cursor.fetchone()[0]

        nowdata = datetime.now()-timedelta(days=60)
        self.cursor.execute("SELECT t1.Id as 'ID', t1.JobId as 'JOB ID', t1.MSGId as 'MSG ID',CONVERT(varchar, t1.TouchTime, 105) AS 'DEC DATE', SUBSTRING(t1.DeclarationType, 1, CHARINDEX(':', t1.DeclarationType) - 1) AS 'DEC TYPE', t1.TouchUser AS 'CREATE', t2.TradeNetMailboxID AS 'DEC ID', CONVERT(varchar, t1.DepartureDate, 105) AS ETD,t1.PermitNumber AS 'PERMIT NO',  t3.OutUserName + ' ' + t3.OutUserName1 AS 'EXPORTER',  STUFF((SELECT distinct(', ' + US.OutHAWBOBL) FROM OutItemDtl US   WHERE US.PermitId = t1.PermitId  FOR XML PATH('')), 1, 1, '') 'HAWB',CASE WHEN  t1.OutwardTransportMode = '4 : Air' THEN t1.OutMasterAirwayBill WHEN t1.OutwardTransportMode = '1 : Sea' THEN t1.OutOceanBillofLadingNo ELSE ''  END AS 'MAWB/OBL',t1.DischargePort as POD,CASE WHEN  t1.COType = '--Select--' THEN ''    WHEN t1.COType != '' THEN t1.COType ELSE ''  END as 'CO TYPE',CASE WHEN  t1.CerDetailtype1 = '--Select--' THEN '-' WHEN t1.CerDetailtype1 != ''  THEN t1.CerDetailtype1 ELSE ''  END as 'CERT TYPE',t1.CertificateNumber as 'CERT NO', t1.MessageType as 'MSG TYPE', t1.OutwardTransportMode as TPT,t1.PreviousPermit as 'PRE PMT',t1.GrossReference as 'X REF', t1.InternalRemarks as 'INT REM', t1.Status as 'STATUS' FROM OutHeaderTbl AS t1 INNER JOIN DeclarantCompany AS t2   ON t1.DeclarantCompanyCode = t2.Code  INNER JOIN OutExporter AS t3 ON t1.ExporterCompanyCode = t3.OutUserCode    INNER JOIN OutInvoiceDtl AS t5 ON t1.PermitId = t5.PermitId  INNER JOIN ManageUser AS t6 ON t6.UserId = t1.TouchUser  where t6.AccountId = '" + AccountId + "' and convert(varchar,t1.TouchTime,111)>='"+ nowdata.strftime("%Y/%m/%d")+ "' GROUP BY t1.Id, t1.JobId, t1.MSGId, t1.TouchTime, t1.TouchUser, t1.DeclarationType,  t1.DepartureDate, t1.PermitId,t1.PermitNumber,t1.PreviousPermit, t1.OutwardTransportMode, t1.OutMasterAirwayBill, t1.OutOceanBillofLadingNo, t1.DischargePort, t1.MessageType, t1.InwardTransportMode, t1.PreviousPermit,t1.COType,t1.CerDetailtype1,t1.CurrencyCode, t1.InternalRemarks,t1.CertificateNumber, t1.Status, t2.TradeNetMailboxID, t3.OutUserName, t3.OutUserName1,t6.AccountId,t2.DeclarantName,t1.InwardTransportMode, t1.ReleaseLocation,t1.RecepitLocation ,t1.DeclarningFor ,t1.InwardTransportMode,t1.License ,t1.GrossReference,t1.INHAWB, t1.DischargePort ,t1.MasterAirwayBill,t1.OceanBillofLadingNo order by t1.Id Desc")#t1.Status != 'DEL' AND
        
        self.HeaderInNon = self.cursor.fetchall()

        result = (pd.DataFrame(list(self.HeaderInNon), columns=['ID', 'JOBID', 'MSGID', 'DECDATE', 'DECTYPE', 'CREATE', 'DECID', 'ETD', 'PERMITNO', 'EXPORTER', 'HAWB', 'MAWBOBL', 'POD', 'COTYPE', 'CERTTYPE', 'CERTNO', 'MSGTYPE', 'TPT', 'PREPMT', 'XREF', 'INTREM', 'STATUS'])).to_dict('records')

        return JsonResponse(result, safe=False)

class OutNew(View,SqlDb): 
    def __init__(self):
        SqlDb.__init__(self)
       
    def get(self,request):
        Username = request.session['Username'] 

        refDate = datetime.now().strftime("%Y%m%d")
        jobDate = datetime.now().strftime("%Y-%m-%d")

        self.cursor.execute("SELECT AccountId FROM ManageUser WHERE UserName = '{}' ".format(Username))
       
        AccountId = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) + 1  FROM OutHeaderTbl WHERE MSGId LIKE '%{}%' AND MessageType = 'OUTDEC' ".format(refDate))
        self.RefId = ("%03d" % self.cursor.fetchone()[0])

        self.cursor.execute("SELECT COUNT(*) + 1  FROM PermitCount WHERE TouchTime LIKE '%{}%' AND AccountId = '{}' ".format(jobDate,AccountId))
        self.JobIdCount = self.cursor.fetchone()[0]

        self.JobId = f"K{datetime.now().strftime('%y%m%d')}{'%05d' % self.JobIdCount}" 

        self.MsgId = f"{datetime.now().strftime('%Y%m%d')}{'%04d' % self.JobIdCount}"

        self.PermitIdInNon = f"{Username}{refDate}{self.RefId}"

        self.cursor.execute("select Top 1 manageuser.LoginStatus,manageuser.DateLastUpdated,manageuser.MailBoxId,manageuser.SeqPool,SequencePool.StartSequence,DeclarantCompany.TradeNetMailboxID,DeclarantCompany.DeclarantName,DeclarantCompany.DeclarantCode,DeclarantCompany.DeclarantTel,DeclarantCompany.CRUEI,DeclarantCompany.Code,DeclarantCompany.name,DeclarantCompany.name1 from manageuser inner join SequencePool on manageuser.SeqPool=SequencePool.Description inner join DeclarantCompany on DeclarantCompany.TradeNetMailboxID=ManageUser.MailBoxId where ManageUser.UserId='" + Username + "'")
        InNonHeadData = self.cursor.fetchone()

        context = { 
            "UserName" : Username,
            "PermitId":self.PermitIdInNon,
            "JobId" : self.JobId,
            "RefId" : self.RefId,
            "MsgId" : self.MsgId,
            "AccountId" : AccountId,
            "LoginStatus" : InNonHeadData[0],
            "PermitNumber" : "",
            "prmtStatus" : "",
            "DateLastUpdated" : InNonHeadData[1],
            "MailBoxId" : InNonHeadData[2],
            "SeqPool" : InNonHeadData[3],
            "StartSequence" : InNonHeadData[4],
            "TradeNetMailboxID" : InNonHeadData[5],
            "DeclarantName" : InNonHeadData[6],
            "DeclarantCode" : InNonHeadData[7],
            "DeclarantTel" : InNonHeadData[8],
            "CRUEI" : InNonHeadData[9],
            "Code" : InNonHeadData[10],
            "name" : InNonHeadData[11],
            "name1" : InNonHeadData[12],
            'DeclarationType':CommonMaster.objects.filter(TypeId=15, StatusId=1).order_by("Name"),
            'CargoType': CommonMaster.objects.filter(TypeId=2, StatusId=1),
            'OutWardTransportMode': CommonMaster.objects.filter(TypeId=3, StatusId=1).order_by('Name'),
            'DeclaringFor': CommonMaster.objects.filter(TypeId=81, StatusId=1).order_by('Name'),
            'BgIndicator': CommonMaster.objects.filter(TypeId=4, StatusId=1).order_by('Name'),
            'DocumentAttachmentType': CommonMaster.objects.filter(TypeId=5, StatusId=1).order_by('Name'),
            'CoType': CommonMaster.objects.filter(TypeId=16, StatusId=1).order_by('Name'),
            'CertificateType': CommonMaster.objects.filter(TypeId=17, StatusId=1).order_by('Name'),
            'Currency': Currency.objects.filter().order_by('Currency'),
            'TotalOuterPack': CommonMaster.objects.filter(TypeId=10, StatusId=1).order_by('Name'),
            'InvoiceTermType': CommonMaster.objects.filter(TypeId=7, StatusId=1).order_by('Name'),
            'Making': CommonMaster.objects.filter(TypeId=12, StatusId=1).order_by('Name'),
            'VesselType': CommonMaster.objects.filter(TypeId=14, StatusId=1).order_by('Name'),
        }
        return render(request, 'Out/OutNew.html',context)

class OutParty(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)
        self.Partycontext = {}

        self.cursor.execute("SELECT OutUserCode,OutUserName,OutUserName1,OutUserCRUEI,OutUserAddress,OutUserAddress1,OutUserCity,OutUserSubCode,OutUserSub,OutUserPostal,OutUserCountry FROM OutExporter WHERE Status = 'Active' ")
        self.Partycontext.update({
            "exporter" : (pd.DataFrame(list(self.cursor.fetchall()), columns=['OutUserCode','OutUserName','OutUserName1','OutUserCRUEI','OutUserAddress','OutUserAddress1','OutUserCity','OutUserSubCode','OutUserSub','OutUserPostal','OutUserCountry'])).to_dict('records')
        })

        
    def get(self,request):       
        return JsonResponse(self.Partycontext)

class PartyLoad(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)
        self.Partycontext = {}

        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM OutImporter WHERE status = 'Active' ORDER BY Name ")
        self.Partycontext.update({
            "importer" : (pd.DataFrame(list(self.cursor.fetchall()), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),
        })

        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM InwardCarrierAgent WHERE status = 'Active' ORDER BY Name")
        self.Partycontext.update({
            "inward" : (pd.DataFrame(list(self.cursor.fetchall()), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),
        })

        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM OutwardCarrierAgent WHERE status = 'Active' ORDER BY Name") 
        self.Partycontext.update({
            "outward" : (pd.DataFrame(list(self.cursor.fetchall()), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records'),
        })
 
        self.cursor.execute("SELECT Code,Name,Name1,CRUEI FROM FreightForwarder WHERE status = 'Active' ORDER BY Name")
        self.Partycontext.update({
            "fright" : (pd.DataFrame(list(self.cursor.fetchall()), columns=["Code", "Name", "Name1","CRUEI"])).to_dict('records')
        })

        self.cursor.execute("SELECT ConsigneeCode,ConsigneeName,ConsigneeName1,ConsigneeCRUEI,ConsigneeAddress,ConsigneeAddress1,ConsigneeCity,ConsigneeSub,ConsigneeSubDivi,ConsigneePostal,ConsigneeCountry FROM OutConsignee ORDER BY ConsigneeName") 
        self.Partycontext.update({
            "consign" : (pd.DataFrame(list(self.cursor.fetchall()), columns=["ConsigneeCode", "ConsigneeName", "ConsigneeName1","ConsigneeCRUEI","ConsigneeAddress", "ConsigneeAddress1", "ConsigneeCity","ConsigneeSub","ConsigneeSubDivi","ConsigneePostal","ConsigneeCountry"])).to_dict('records')
        })

    def get(self,request):
        return JsonResponse(self.Partycontext)
    
class ParytManFacture(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)
        self.Partycontext = {}
        self.cursor.execute("SELECT ManufacturerCode,ManufacturerName,ManufacturerName1,ManufacturerCRUEI,ManufacturerAddress,ManufacturerAddress1,ManufacturerCity,ManufacturerSubDivi,ManufacturerSub,ManufacturerPostal,ManufacturerCountry FROM OutManufacturer where Status = 'Active' ")
        self.Partycontext.update({
            'manfacture' : (pd.DataFrame(list(self.cursor.fetchall()),columns=['ManufacturerCode','ManufacturerName','ManufacturerName1','ManufacturerCRUEI','ManufacturerAddress','ManufacturerAddress1','ManufacturerCity','ManufacturerSubDivi','ManufacturerSub','ManufacturerPostal','ManufacturerCountry'])).to_dict('records')
        })

    def get(self,request):
        return JsonResponse(self.Partycontext)
    
class CargoLocations(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)
        self.Partycontext = {}

        self.cursor.execute("SELECT Code,Description FROM ReleaseLocation order by Id")
        self.Partycontext.update({
            'releaseLocation' : (pd.DataFrame(list(self.cursor.fetchall()),columns=['Code','Description'])).to_dict('records')
        })

        self.cursor.execute("SELECT Code,Description FROM ReceiptLocation order by Id")
        self.Partycontext.update({
            'reciptLocation' : (pd.DataFrame(list(self.cursor.fetchall()),columns=['Code','Description'])).to_dict('records')
        })
        
        self.cursor.execute("select * from LoadingPort")
        headers = [i[0] for i in self.cursor.description]
        self.Partycontext.update({
            "loadingPort" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')
        })
        
    def get(self,request):
        return JsonResponse(self.Partycontext)
    
class OutInvoice(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)
        self.Partycontext = {}
         
    def get(self,request,Permit):
        self.cursor.execute(f"select * from OutInvoiceDtl WHERE PermitId = '{Permit}' ORDER BY SNo")
        headers = [i[0] for i in self.cursor.description]
        self.Partycontext.update({
            "invoice" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')
        })
        return JsonResponse(self.Partycontext)
    
    def post(self,request):
        SNo = request.POST.get('SNo')
        PermitId = request.POST.get('PermitId')
        message = ""
        if request.POST.get('method') == "DELETE":
            print("this is delete")
            self.cursor.execute("DELETE FROM OutInvoiceDtl WHERE PermitId = '{}' AND SNo = {}".format(request.POST.get("PermitId"),request.POST.get("SNo")))
            self.conn.commit()

            self.cursor.execute("SELECT SNo ,PermitId FROM OutInvoiceDtl WHERE PermitId = '{}' ORDER BY SNo".format(request.POST.get("PermitId")))
            for ind in range(1,len(self.cursor.fetchall())+1):
                self.cursor.execute("UPDATE OutInvoiceDtl SET SNo = '{}' WHERE PermitId = '{}' ".format(ind,request.POST.get("PermitId")))
            self.conn.commit()
        else:
            try:
                self.cursor.execute(f"SELECT PermitId,SNo FROM OutInvoiceDtl WHERE PermitId = '{PermitId}' AND SNo = '{SNo}'")
                if self.cursor.fetchone():
                    InvoiceUpd = f"UPDATE OutInvoiceDtl SET SNo = %s ,InvoiceNo = %s ,InvoiceDate = %s ,TermType = %s ,AdValoremIndicator = %s ,PreDutyRateIndicator = %s ,SupplierImporterRelationship = %s ,SupplierCode = %s ,ExportPartyCode = %s ,TICurrency = %s ,TIExRate = %s ,TIAmount = %s ,TISAmount = %s ,OTCCharge = %s ,OTCCurrency = %s ,OTCExRate = %s ,OTCAmount = %s ,OTCSAmount = %s ,FCCharge = %s ,FCCurrency = %s ,FCExRate = %s ,FCAmount = %s ,FCSAmount = %s ,ICCharge = %s ,ICCurrency = %s ,ICExRate = %s ,ICAmount = %s ,ICSAmount = %s ,CIFSUMAmount = %s ,GSTPercentage = %s ,GSTSUMAmount = %s ,MessageType = %s ,PermitId = %s ,TouchUser = %s ,TouchTime = %s WHERE PermitId = '{PermitId}' AND SNo = '{SNo}' "
                    InvoiceVal = (request.POST.get('SNo'),request.POST.get('InvoiceNo'),request.POST.get('InvoiceDate'),request.POST.get('TermType'),request.POST.get('AdValoremIndicator'),request.POST.get('PreDutyRateIndicator'),request.POST.get('SupplierImporterRelationship'),request.POST.get('SupplierCode'),request.POST.get('ExportPartyCode'),request.POST.get('TICurrency'),request.POST.get('TIExRate'),request.POST.get('TIAmount'),request.POST.get('TISAmount'),request.POST.get('OTCCharge'),request.POST.get('OTCCurrency'),request.POST.get('OTCExRate'),request.POST.get('OTCAmount'),request.POST.get('OTCSAmount'),request.POST.get('FCCharge'),request.POST.get('FCCurrency'),request.POST.get('FCExRate'),request.POST.get('FCAmount'),request.POST.get('FCSAmount'),request.POST.get('ICCharge'),request.POST.get('ICCurrency'),request.POST.get('ICExRate'),request.POST.get('ICAmount'),request.POST.get('ICSAmount'),request.POST.get('CIFSUMAmount'),request.POST.get('GSTPercentage'),request.POST.get('GSTSUMAmount'),request.POST.get('MessageType'),request.POST.get('PermitId'),str(request.session['Username']).upper(),request.POST.get('TouchTime'))
                    self.cursor.execute(InvoiceUpd,InvoiceVal)
                    message = "Successfully Inserted"
                else:
                    InvoiceData = "INSERT INTO OutInvoiceDtl (SNo,InvoiceNo,InvoiceDate,TermType,AdValoremIndicator,PreDutyRateIndicator,SupplierImporterRelationship,SupplierCode,ExportPartyCode,TICurrency,TIExRate,TIAmount,TISAmount,OTCCharge,OTCCurrency,OTCExRate,OTCAmount,OTCSAmount,FCCharge,FCCurrency,FCExRate,FCAmount,FCSAmount,ICCharge,ICCurrency,ICExRate,ICAmount,ICSAmount,CIFSUMAmount,GSTPercentage,GSTSUMAmount,MessageType,PermitId,TouchUser,TouchTime) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                    InvoiceVal = (request.POST.get('SNo'),request.POST.get('InvoiceNo'),request.POST.get('InvoiceDate'),request.POST.get('TermType'),request.POST.get('AdValoremIndicator'),request.POST.get('PreDutyRateIndicator'),request.POST.get('SupplierImporterRelationship'),request.POST.get('SupplierCode'),request.POST.get('ExportPartyCode'),request.POST.get('TICurrency'),request.POST.get('TIExRate'),request.POST.get('TIAmount'),request.POST.get('TISAmount'),request.POST.get('OTCCharge'),request.POST.get('OTCCurrency'),request.POST.get('OTCExRate'),request.POST.get('OTCAmount'),request.POST.get('OTCSAmount'),request.POST.get('FCCharge'),request.POST.get('FCCurrency'),request.POST.get('FCExRate'),request.POST.get('FCAmount'),request.POST.get('FCSAmount'),request.POST.get('ICCharge'),request.POST.get('ICCurrency'),request.POST.get('ICExRate'),request.POST.get('ICAmount'),request.POST.get('ICSAmount'),request.POST.get('CIFSUMAmount'),request.POST.get('GSTPercentage'),request.POST.get('GSTSUMAmount'),request.POST.get('MessageType'),request.POST.get('PermitId'),str(request.session['Username']).upper(),request.POST.get('TouchTime'))
                    self.cursor.execute(InvoiceData,InvoiceVal)  
                    message = "Successfully Insertd"  
                self.conn.commit()
            except :
                message = "Sorry Did not saved somthing error"
        
        self.cursor.execute(f"select * from OutInvoiceDtl WHERE PermitId = '{PermitId}' ORDER BY SNo")
        headers = [i[0] for i in self.cursor.description]
        self.Partycontext.update({
            "invoice" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records'),
            "message":message
        })
        return JsonResponse(self.Partycontext)
    
    
    
class OutItemInhouse(View,SqlDb):
    def get(self,request):
        SqlDb.__init__(self)
        context = {}
        self.cursor.execute("select * from InhouseItemCode where DeclType='OUT'")
        headers = [i[0] for i in self.cursor.description]
        context.update({
                "inhouse" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')
        })
        self.cursor.execute("select * from ChkHsCode")
        headers = [i[0] for i in self.cursor.description]
        context.update({
                "ChkHsCode" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')
        })

        self.cursor.execute("select * from Country")
        headers = [i[0] for i in self.cursor.description]
        context.update({
                "country" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')
        })

        return JsonResponse(context)
    
class OutHscode(View,SqlDb):
    def get(self,request):
        SqlDb.__init__(self)
        self.cursor.execute("select * from HSCode")
        headers = [i[0] for i in self.cursor.description] 
        return JsonResponse({"hscode" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')})
    
class OutItem(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)

    def get(self,request,Permit):
        
        context = {}
        
        self.cursor.execute(f"select * from OutCASCDtl WHERE PermitId = '{Permit}' ORDER BY ItemNo")
        headers = [i[0] for i in self.cursor.description]
        context.update({"casc" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')})
        
        self.cursor.execute(f"select * from OutItemDtl WHERE PermitId = '{Permit}' ORDER BY ItemNo")
        headers = [i[0] for i in self.cursor.description]
        context.update({"item" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')})
        return JsonResponse(context)
    
    def post(self,request):
        self.cursor.execute(f"DELETE FROM OutCASCDtl WHERE ItemNo = '{request.POST.get('ItemNo')}' AND PermitId = '{request.POST.get('PermitId')}'")
        self.conn.commit()
        
        context = {}
        message = ""
        
        cascQry = "INSERT INTO OutCASCDtl (ItemNo,ProductCode,Quantity,ProductUOM,RowNo,CascCode1,CascCode2,CascCode3,PermitId,MessageType,TouchUser,TouchTime,CASCId,EndUserDes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for casc in json.loads(request.POST.get('CascDatas')):
            cascVal = (request.POST.get('ItemNo'),casc['ProductCode'],casc['Quantity'],casc['ProductUOM'],casc['RowNo'],casc['CascCode1'],casc['CascCode2'],casc['CascCode3'],request.POST.get('PermitId'),request.POST.get('MessageType'),str(request.session['Username']).upper(),datetime.now(),casc['CASCId'],casc['EndUserDes'])
            self.cursor.execute(cascQry,cascVal)
        self.conn.commit()
        
        self.cursor.execute(f"select * from OutCASCDtl WHERE PermitId = '{request.POST.get('PermitId')}' ORDER BY ItemNo")
        headers = [i[0] for i in self.cursor.description]
        context.update({"casc" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')})
        
        self.cursor.execute(f"SELECT ItemNo,PermitId FROM OutItemDtl WHERE ItemNo = '{request.POST.get('ItemNo')}' AND PermitId = '{request.POST.get('PermitId')}' ")
        if self.cursor.fetchone() is None:
            try:
                Qry = "INSERT INTO OutItemDtl (ItemNo,PermitId,MessageType,HSCode,Description,DGIndicator,Contry,EndUserDescription,Brand,Model,InHAWBOBL,OutHAWBOBL,DutiableQty,DutiableUOM,TotalDutiableQty,TotalDutiableUOM,InvoiceQuantity,HSQty,HSUOM,AlcoholPer,InvoiceNo,ChkUnitPrice,UnitPrice,UnitPriceCurrency,ExchangeRate,SumExchangeRate,TotalLineAmount,InvoiceCharges,CIFFOB,OPQty,OPUOM,IPQty,IPUOM,InPqty,InPUOM,ImPQty,ImPUOM,PreferentialCode,GSTRate,GSTUOM,GSTAmount,ExciseDutyRate,ExciseDutyUOM,ExciseDutyAmount,CustomsDutyRate,CustomsDutyUOM,CustomsDutyAmount,OtherTaxRate,OtherTaxUOM,OtherTaxAmount,CurrentLot,PreviousLot,Making,ShippingMarks1,ShippingMarks2,ShippingMarks3,ShippingMarks4,CerItemQty,CerItemUOM,CIFValOfCer,ManufactureCostDate,TexCat,TexQuotaQty,TexQuotaUOM,CerInvNo,CerInvDate,OriginOfCer,HSCodeCer,PerContent,CertificateDescription,TouchUser,TouchTime,VehicleType,OptionalChrgeUOM,EngineCapcity,Optioncahrge,OptionalSumtotal,OptionalSumExchage,EngineCapUOM,orignaldatereg) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                val = (request.POST.get('ItemNo'),request.POST.get('PermitId'),request.POST.get('MessageType'),request.POST.get('HSCode'),request.POST.get('Description'),request.POST.get('DGIndicator'),request.POST.get('Contry'),request.POST.get('EndUserDescription'),request.POST.get('Brand'),request.POST.get('Model'),request.POST.get('InHAWBOBL'),request.POST.get('OutHAWBOBL'),request.POST.get('DutiableQty'),request.POST.get('DutiableUOM'),request.POST.get('TotalDutiableQty'),request.POST.get('TotalDutiableUOM'),request.POST.get('InvoiceQuantity'),request.POST.get('HSQty'),request.POST.get('HSUOM'),request.POST.get('AlcoholPer'),request.POST.get('InvoiceNo'),request.POST.get('ChkUnitPrice'),request.POST.get('UnitPrice'),request.POST.get('UnitPriceCurrency'),request.POST.get('ExchangeRate'),request.POST.get('SumExchangeRate'),request.POST.get('TotalLineAmount'),request.POST.get('InvoiceCharges'),request.POST.get('CIFFOB'),request.POST.get('OPQty'),request.POST.get('OPUOM'),request.POST.get('IPQty'),request.POST.get('IPUOM'),request.POST.get('InPqty'),request.POST.get('InPUOM'),request.POST.get('ImPQty'),request.POST.get('ImPUOM'),request.POST.get('PreferentialCode'),request.POST.get('GSTRate'),request.POST.get('GSTUOM'),request.POST.get('GSTAmount'),request.POST.get('ExciseDutyRate'),request.POST.get('ExciseDutyUOM'),request.POST.get('ExciseDutyAmount'),request.POST.get('CustomsDutyRate'),request.POST.get('CustomsDutyUOM'),request.POST.get('CustomsDutyAmount'),request.POST.get('OtherTaxRate'),request.POST.get('OtherTaxUOM'),request.POST.get('OtherTaxAmount'),request.POST.get('CurrentLot'),request.POST.get('PreviousLot'),request.POST.get('Making'),request.POST.get('ShippingMarks1'),request.POST.get('ShippingMarks2'),request.POST.get('ShippingMarks3'),request.POST.get('ShippingMarks4'),request.POST.get('CerItemQty'),request.POST.get('CerItemUOM'),request.POST.get('CIFValOfCer'),request.POST.get('ManufactureCostDate'),request.POST.get('TexCat'),request.POST.get('TexQuotaQty'),request.POST.get('TexQuotaUOM'),request.POST.get('CerInvNo'),request.POST.get('CerInvDate'),request.POST.get('OriginOfCer'),request.POST.get('HSCodeCer'),request.POST.get('PerContent'),request.POST.get('CertificateDescription'),str(request.session['Username']).upper(),datetime.now(),request.POST.get('VehicleType'),request.POST.get('OptionalChrgeUOM'),request.POST.get('EngineCapcity'),request.POST.get('Optioncahrge'),request.POST.get('OptionalSumtotal'),request.POST.get('OptionalSumExchage'),request.POST.get('EngineCapUOM'),request.POST.get('orignaldatereg'))
                self.cursor.execute(Qry,val)
                message = "Inserted Successfully...!"
            except Exception as e:
                print(e)
                message = "Did not saved...!"
        else:
            try:
                Val = (request.POST.get('ItemNo'),request.POST.get('PermitId'),request.POST.get('MessageType'),request.POST.get('HSCode'),request.POST.get('Description'),request.POST.get('DGIndicator'),request.POST.get('Contry'),request.POST.get('EndUserDescription'),request.POST.get('Brand'),request.POST.get('Model'),request.POST.get('InHAWBOBL'),request.POST.get('OutHAWBOBL'),request.POST.get('DutiableQty'),request.POST.get('DutiableUOM'),request.POST.get('TotalDutiableQty'),request.POST.get('TotalDutiableUOM'),request.POST.get('InvoiceQuantity'),request.POST.get('HSQty'),request.POST.get('HSUOM'),request.POST.get('AlcoholPer'),request.POST.get('InvoiceNo'),request.POST.get('ChkUnitPrice'),request.POST.get('UnitPrice'),request.POST.get('UnitPriceCurrency'),request.POST.get('ExchangeRate'),request.POST.get('SumExchangeRate'),request.POST.get('TotalLineAmount'),request.POST.get('InvoiceCharges'),request.POST.get('CIFFOB'),request.POST.get('OPQty'),request.POST.get('OPUOM'),request.POST.get('IPQty'),request.POST.get('IPUOM'),request.POST.get('InPqty'),request.POST.get('InPUOM'),request.POST.get('ImPQty'),request.POST.get('ImPUOM'),request.POST.get('PreferentialCode'),request.POST.get('GSTRate'),request.POST.get('GSTUOM'),request.POST.get('GSTAmount'),request.POST.get('ExciseDutyRate'),request.POST.get('ExciseDutyUOM'),request.POST.get('ExciseDutyAmount'),request.POST.get('CustomsDutyRate'),request.POST.get('CustomsDutyUOM'),request.POST.get('CustomsDutyAmount'),request.POST.get('OtherTaxRate'),request.POST.get('OtherTaxUOM'),request.POST.get('OtherTaxAmount'),request.POST.get('CurrentLot'),request.POST.get('PreviousLot'),request.POST.get('Making'),request.POST.get('ShippingMarks1'),request.POST.get('ShippingMarks2'),request.POST.get('ShippingMarks3'),request.POST.get('ShippingMarks4'),request.POST.get('CerItemQty'),request.POST.get('CerItemUOM'),request.POST.get('CIFValOfCer'),request.POST.get('ManufactureCostDate'),request.POST.get('TexCat'),request.POST.get('TexQuotaQty'),request.POST.get('TexQuotaUOM'),request.POST.get('CerInvNo'),request.POST.get('CerInvDate'),request.POST.get('OriginOfCer'),request.POST.get('HSCodeCer'),request.POST.get('PerContent'),request.POST.get('CertificateDescription'),str(request.session['Username']).upper(),datetime.now(),request.POST.get('VehicleType'),request.POST.get('OptionalChrgeUOM'),request.POST.get('EngineCapcity'),request.POST.get('Optioncahrge'),request.POST.get('OptionalSumtotal'),request.POST.get('OptionalSumExchage'),request.POST.get('EngineCapUOM'),request.POST.get('orignaldatereg'))
                PermitId = request.POST.get('PermitId')
                ItemNo = request.POST.get('ItemNo')
                Qry = f"UPDATE OutItemDtl SET ItemNo = %s,PermitId = %s,MessageType = %s,HSCode = %s,Description = %s,DGIndicator = %s,Contry = %s,EndUserDescription = %s,Brand = %s,Model = %s,InHAWBOBL = %s,OutHAWBOBL = %s,DutiableQty = %s,DutiableUOM = %s,TotalDutiableQty = %s,TotalDutiableUOM = %s,InvoiceQuantity = %s,HSQty = %s,HSUOM = %s,AlcoholPer = %s,InvoiceNo = %s,ChkUnitPrice = %s,UnitPrice = %s,UnitPriceCurrency = %s,ExchangeRate = %s,SumExchangeRate = %s,TotalLineAmount = %s,InvoiceCharges = %s,CIFFOB = %s,OPQty = %s,OPUOM = %s,IPQty = %s,IPUOM = %s,InPqty = %s,InPUOM = %s,ImPQty = %s,ImPUOM = %s,PreferentialCode = %s,GSTRate = %s,GSTUOM = %s,GSTAmount = %s,ExciseDutyRate = %s,ExciseDutyUOM = %s,ExciseDutyAmount = %s,CustomsDutyRate = %s,CustomsDutyUOM = %s,CustomsDutyAmount = %s,OtherTaxRate = %s,OtherTaxUOM = %s,OtherTaxAmount = %s,CurrentLot = %s,PreviousLot = %s,Making = %s,ShippingMarks1 = %s,ShippingMarks2 = %s,ShippingMarks3 = %s,ShippingMarks4 = %s,CerItemQty = %s,CerItemUOM = %s,CIFValOfCer = %s,ManufactureCostDate = %s,TexCat = %s,TexQuotaQty = %s,TexQuotaUOM = %s,CerInvNo = %s,CerInvDate = %s,OriginOfCer = %s,HSCodeCer = %s,PerContent = %s,CertificateDescription = %s,TouchUser = %s,TouchTime = %s,VehicleType = %s,OptionalChrgeUOM = %s,EngineCapcity = %s,Optioncahrge = %s,OptionalSumtotal = %s,OptionalSumExchage = %s,EngineCapUOM = %s,orignaldatereg = %s WHERE PermitId = '{PermitId}' AND ItemNo = '{ItemNo}'  "
                self.cursor.execute(Qry,Val)
                message = "Updated Successfully...!"
            except Exception as e:
                print("the Eror is : ",e)
                message = "Did not Updated"
        self.conn.commit()
        
        context.update({"message" : message})

        self.cursor.execute(f"select * from OutItemDtl WHERE PermitId = '{request.POST.get('PermitId')}' ORDER BY ItemNo")
        headers = [i[0] for i in self.cursor.description]
        context.update({"item" : (pd.DataFrame(list(self.cursor.fetchall()), columns=headers)).to_dict('records')})
        return JsonResponse(context)
    
    
def outItemDelete(request):
    data = json.loads(request.POST.get('Ids'))
    try:
        db = SqlDb()
        db.cursor.execute("DELETE FROM OutItemDtl WHERE Id ")
    except : print("errror")

    ItemValue = json.loads(request.POST.get('Ids'))

    values_str = ', '.join(map(str, ItemValue))

    query1 = f"DELETE FROM OutItemDtl WHERE ItemNo IN ({values_str}) AND PermitId = '{request.POST.get('PermitId')}' "
    db.cursor.execute(query1)

    query2 = f"DELETE FROM OutCASCDtl WHERE ItemNo IN ({values_str}) AND PermitId = '{request.POST.get('PermitId')}' "
    db.cursor.execute(query2)

    db.conn.commit()

    db.cursor.execute("SELECT ItemNo,PermitId FROM InNonItemDtl WHERE PermitId = '{}' ORDER BY ItemNo".format(request.POST.get('PermitId')))

    Ic = 1 
    for itm in db.cursor.fetchall():
        db.cursor.execute("UPDATE InNonItemDtl SET ItemNo = '{}' WHERE PermitId = '{}' AND  ItemNo = '{}' ".format(Ic,request.POST.get('PermitId'),itm[0]))
        db.cursor.execute("UPDATE INNONCASCDtl SET ItemNo = '{}' WHERE PermitId = '{}' AND  ItemNo = '{}' ".format(Ic,request.POST.get('PermitId'),itm[0]))
        Ic += 1

    db.conn.commit()
    
    context = {}
    db.cursor.execute(f"select * from OutCASCDtl WHERE PermitId = '{request.POST.get('PermitId')}' ORDER BY ItemNo")
    headers = [i[0] for i in db.cursor.description]
    context.update({"casc" : (pd.DataFrame(list(db.cursor.fetchall()), columns=headers)).to_dict('records')})
    
    db.cursor.execute(f"select * from OutItemDtl WHERE PermitId = '{request.POST.get('PermitId')}' ORDER BY ItemNo")
    headers = [i[0] for i in db.cursor.description]
    context.update({"item" : (pd.DataFrame(list(db.cursor.fetchall()), columns=headers)).to_dict('records')})
    return JsonResponse(context)

    
class outSaveSubmit(View,SqlDb):
    def __init__(self):
        SqlDb.__init__(self)
    
    def post(self,request):
        print("Welcome")
        data = (request.POST.get('Refid'),request.POST.get('JobId'),request.POST.get('MSGId'),request.POST.get('PermitId'),request.POST.get('TradeNetMailboxID'),request.POST.get('MessageType'),request.POST.get('DeclarationType'),request.POST.get('PreviousPermit'),request.POST.get('CargoPackType'),request.POST.get('InwardTransportMode'),request.POST.get('OutwardTransportMode'),request.POST.get('BGIndicator'),request.POST.get('SupplyIndicator'),request.POST.get('ReferenceDocuments'),request.POST.get('License'),request.POST.get('COType'),request.POST.get('Entryyear'),request.POST.get('GSPDonorCountry'),request.POST.get('CerDetailtype1'),request.POST.get('CerDetailCopies1'),request.POST.get('CerDetailtype2'),request.POST.get('CerDetailCopies2'),request.POST.get('PerCommon'),request.POST.get('CurrencyCode'),request.POST.get('AddCerDtl'),request.POST.get('TransDtl'),request.POST.get('Recipient'),request.POST.get('DeclarantCompanyCode'),request.POST.get('ExporterCompanyCode'),request.POST.get('Inwardcarriercode'),request.POST.get('OutwardCarrierAgentCode'),request.POST.get('FreightForwarderCode'),request.POST.get('ImporterCompanyCode'),request.POST.get('InwardCarrierAgentCode'),request.POST.get('CONSIGNEECode'),request.POST.get('EndUserCode'),request.POST.get('Manufacturer'),request.POST.get('ArrivalDate'),request.POST.get('ArrivalTime'),request.POST.get('LoadingPortCode'),request.POST.get('VoyageNumber'),request.POST.get('VesselName'),request.POST.get('OceanBillofLadingNo'),request.POST.get('ConveyanceRefNo'),request.POST.get('TransportId'),request.POST.get('FlightNO'),request.POST.get('AircraftRegNo'),request.POST.get('MasterAirwayBill'),request.POST.get('ReleaseLocation'),request.POST.get('RecepitLocation'),request.POST.get('StorageLocation'),request.POST.get('BlanketStartDate'),request.POST.get('DepartureDate'),request.POST.get('DepartureTime'),request.POST.get('DischargePort'),request.POST.get('FinalDestinationCountry'),request.POST.get('OutVoyageNumber'),request.POST.get('OutVesselName'),request.POST.get('OutOceanBillofLadingNo'),request.POST.get('VesselType'),request.POST.get('VesselNetRegTon'),request.POST.get('VesselNationality'),request.POST.get('TowingVesselID'),request.POST.get('TowingVesselName'),request.POST.get('NextPort'),request.POST.get('LastPort'),request.POST.get('OutConveyanceRefNo'),request.POST.get('OutTransportId'),request.POST.get('OutFlightNO'),request.POST.get('OutAircraftRegNo'),request.POST.get('OutMasterAirwayBill'),request.POST.get('TotalOuterPack'),request.POST.get('TotalOuterPackUOM'),request.POST.get('TotalGrossWeight'),request.POST.get('TotalGrossWeightUOM'),request.POST.get('GrossReference'),request.POST.get('TradeRemarks'),request.POST.get('InternalRemarks'),request.POST.get('DeclareIndicator'),request.POST.get('NumberOfItems'),request.POST.get('TotalCIFFOBValue'),request.POST.get('TotalGSTTaxAmt'),request.POST.get('TotalExDutyAmt'),request.POST.get('TotalCusDutyAmt'),request.POST.get('TotalODutyAmt'),request.POST.get('TotalAmtPay'),request.POST.get('Status'),request.POST.get('TouchUser'),request.POST.get('TouchTime'),request.POST.get('PermitNumber'),request.POST.get('prmtStatus'),request.POST.get('ResLoaName'),request.POST.get('RepLocName'),request.POST.get('RecepitLocName'),request.POST.get('outHAWB'),request.POST.get('INHAWB'),request.POST.get('CertificateNumber'),request.POST.get('Defrentprinting'),request.POST.get('Cnb'),request.POST.get('DeclarningFor'),request.POST.get('MRDate'),request.POST.get('MRTime'))
        print(data)
        return JsonResponse({"message" : "Saved..."})
   