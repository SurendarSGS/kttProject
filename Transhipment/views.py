from django.shortcuts import render
from KttApp.views import SqlDb
from django.views import View
from KttApp.models import *

class TransHome(View):
    def get(self,request):
        context = {
            'CustomiseReport': CustomiseReport.objects.filter(ReportName="IPT", UserName=request.session['Username']).exclude(FiledName='id'),
            'ManageUserMail': ManageUser.objects.filter(Status='Active').order_by('MailBoxId').values_list('MailBoxId', flat=True).distinct(),
            'UserName':request.session['Username']
        }
        return render(request,'Transhipment/Listpage.html',context) 

class TranshList(View,SqlDb):
    def __init__(self): 
        SqlDb.__init__(self)
       
    def get(self,request):
        Username = request.session['Username'] 

        self.cursor.execute("SELECT AccountId FROM ManageUser WHERE UserName = '{}' ".format(Username))
        AccountId = self.cursor.fetchone()[0]

        nowdata = datetime.now()-timedelta(days=60)
        self.cursor.execute("SELECT   t1.Id as 'ID', t1.JobId as 'JOB ID', t1.MSGId as 'MSG ID', CONVERT(varchar, t1.TouchTime, 105) AS 'DEC DATE',SUBSTRING(t1.DeclarationType , 1, CHARINDEX(':', t1.DeclarationType) - 1) AS 'DEC TYPE',t1.TouchUser AS 'CREATE', t2.TradeNetMailboxID AS 'DEC ID', CONVERT(varchar, t1.ArrivalDate, 105) AS ETA, t1.PermitNumber AS 'PERMIT NO', t3.Name +' '+t3.Name1 AS 'IMPORTER',  t1.Inhabl as 'HAWB', CASE  WHEN  t1.InwardTransportMode = '4 : Air' THEN t1.MasterAirwayBill  WHEN t1.InwardTransportMode = '1 : Sea' THEN t1.OceanBillofLadingNo   ELSE '' END AS 'MAWB/OBL',t1.LoadingPortCode as POL, t1.MessageType as 'MSG TYPE', t1.InwardTransportMode as TPT, t1.PreviousPermit as 'PRE PMT',t1.GrossReference as 'X REF', t1.InternalRemarks as 'INT REM',  SUM(t1.TotalGSTTaxAmt) AS 'GST AMT', t1.Status as 'STATUS',case  when  t1.Status='APR' then (case when (select top 1 ConditionCode from InnonPMT where ConditionCode='Z02' and t1.PermitNumber=InnonPMT.PermitNumber)='Z02' or (select top 1 ConditionCode from InnonPMT where ConditionCode='Z18' and t1.PermitNumber=InnonPMT.PermitNumber)='Z18' or (select top 1 ConditionCode from InnonPMT where ConditionCode='Z06' and t1.PermitNumber=InnonPMT.PermitNumber)='Z06' then 'RED' when (select top 1 ConditionCode from InnonPMT where ConditionCode='D6' and t1.PermitNumber=InnonPMT.PermitNumber)='D6' or (select top 1 ConditionCode from InnonPMT where ConditionCode='D3' and t1.PermitNumber=InnonPMT.PermitNumber)='D3' then 'Maroon' else 'Default'  end)  else 'default' end as 'COLOR'  FROM  InNonHeaderTbl AS t1 left JOIN   DeclarantCompany AS t2 ON t1.DeclarantCompanyCode = t2.Code left JOIN InNonImporter AS t3 ON t1.ImporterCompanyCode = t3.Code  left JOIN ManageUser AS t6 ON t6.UserId=t1.TouchUser  where   t6.AccountId='" + AccountId + "' and convert(varchar,t1.TouchTime,111)>='"+ nowdata.strftime("%Y/%m/%d")+ "'  GROUP BY t1.Id, t1.JobId, t1.MSGId, t1.TouchTime, t1.TouchUser,t1.DeclarationType,t1.ArrivalDate, t1.PermitId,	t1.PermitNumber, t1.InwardTransportMode,t1.OutwardTransportMode,t1.MasterAirwayBill,t1.OceanBillofLadingNo, t1.LoadingPortCode, t1.MessageType, t1.InwardTransportMode,t1.PreviousPermit,t1.Inhabl, t1.InternalRemarks, t1.Status, t2.TradeNetMailboxID, 	t3.Name,t3.Name1, t6.AccountId,t1.OutMasterAirwayBill, t1.OutOceanBillofLadingNo,t1.outhbl,t1.OutwardTransportMode,t2.DeclarantName,t1.DepartureDate , t1.DischargePort, t1.GrossReference ,t1.License ,t1.ReleaseLocation ,t1.RecepitLocation ,t1.DeclarningFor,t1.ExporterCompanyCode ORDER BY ID DESC")
    
        self.HeaderInNon = self.cursor.fetchall()

        result = (pd.DataFrame(list(self.HeaderInNon), columns=["id","JobId","MSGId","DECDATE","DECTYPE","CREATE","DECID","ETA","PERMITNO","IMPORTER","HAWB","MAWBOBL","POL","MSGTYPE","TPT","PREPMT","XREF","INTREM","GSTAMT","STATUS","PermitId"])).to_dict('records')

        return JsonResponse(result, safe=False)

