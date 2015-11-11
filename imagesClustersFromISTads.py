import csv
import MySQLdb
import json
import pickle
import time
import happybase

global_var = json.load(open('global_var_all.json'))
isthost=global_var['ist_db_host']
istuser=global_var['ist_db_user']
istpwd=global_var['ist_db_pwd']
istdb=global_var['ist_db_dbname']
localhost=global_var['local_db_host']
localuser=global_var['local_db_user']
localpwd=global_var['local_db_pwd']
localdb=global_var['local_db_dbname']

def getExpanded(imagesid,imageslocation,ad_id):
    print "Extended from imagesid",imagesid
    connection = happybase.Connection('10.1.94.57')
    tab = connection.table('aaron_memex_ht-images')
    exp_adsid=[]
    exp_imagesid=[]
    visited_expimagesid=[]
    queue_images=imagesid
    for oneid in queue_images:
        #onerow=tab.row(str(oneid),columns=('meta:columbia_near_dups','meta:columbia_near_dups_dist','meta:columbia_near_dups_biggest_dbid'))
        onerow=tab.row(str(oneid),columns=('meta:columbia_near_dups','meta:ads_id'))
        print onerow
        visited_expimagesid.extend([oneid])
        if oneid not in imagesid and oneid not in exp_imagesid:
            exp_imagesid.append(oneid)
            oneexp_ad_id=onerow['meta:ads_id']
            exp_adsid.add(oneexp_ad_id)
        neighbors_list=onerow['meta:columbia_near_dups'].rsplit(',')
        for expimg in neighbors_list:
            if expimg not in imagesid and expimg not in exp_imagesid:
                queue_images.extend([expimg])
    return exp_adsid,exp_imagesid

# Get data from CSV
csv_filename='nov2015_qpr_truth__ids_images.csv'
csv_file=open(csv_filename,'rb')
csv_file.readline() # discard header
csvreader = csv.reader(csv_file)
ads_id=[]
clusters_id=[]
images_urls=[]
for row in csvreader:
    #print len(row),":",', '.join(row)
    clusters_id.append(row[0])
    ads_id.append(row[5])
    images_urls.append(row[6].split(";"))
    #print row[6].split(";")
    #time.sleep(10)
print len(ads_id)
#print len(ads_id),ads_id
#print len(images_urls),images_urls

# Get all data from IST database
db=MySQLdb.connect(host=isthost,user=istuser,passwd=istpwd,db=istdb)
c=db.cursor()
sql_withurl='select i.id,i.url,i.location,ads.url,ads.id from images i left join ads on i.ads_id=ads.id where i.location in (%s) and ads.id=(%s) order by i.id;'
sql_nourl='select i.id,i.url,i.location,ads.url,ads.id from images i left join ads on i.ads_id=ads.id where ads.id=(%s) order by i.id;'
all_imagesid=[]
all_extended_imagesid=[]
all_imagesurl=[]
all_imageslocation=[]
all_adsurl=[]
all_adsid=[]



for pos,ad_id in enumerate(ads_id):
    print pos,len(all_adsid)
    print images_urls[pos]
    if len(images_urls[pos])==1 and not images_urls[pos][0]: # empty
        sqlq = sql_nourl % (ad_id,)
	c.execute(sqlq)
    else:
        sqlq = sql_withurl % (', '.join(map(lambda x: '%s', images_urls[pos])),ad_id)
	c.execute(sqlq,images_urls[pos])
    print sqlq
    tmpresult = c.fetchall()
    print tmpresult
    all_adsid.append(ad_id)
    all_adsurl.append([])
    all_imagesid.append([])
    all_expanded_imagesid.append([])
    all_expanded_adsid.append([])
    all_imageslocation.append([])
    all_imagesurl.append(images_urls[pos])
    if len(tmpresult)>0:
      all_adsurl.extend(tmpresult[0][3])      
      for posres,oneres in enumerate(tmpresult):
        print posres,oneres
        print "Found image id",oneres[0]
        all_imagesid[pos].extend([oneres[0]])
        all_imagesurl[pos].extend([oneres[1]])
        all_imageslocation[pos].extend([oneres[2]])
      # Get similar images
      ext_adsid,ext_imagesid=getExpanded(all_imagesid[pos],all_imageslocation[pos],ad_id)
      all_expanded_imagesid[pos].extend(ext_imagesid)
      all_expanded_adsid[pos].extend(ext_adsid)
    else:
	print "Couldn't find images for this ad?",str(ad_id)
    #if len(images_urls[pos])>1 or images_urls[pos][0]: 
	#time.sleep(10)	
db.close()

print len(all_imagesid)
print len(all_adsid)

alldata_istgt={}
alldata_istgt['all_imagesid']=all_imagesid
alldata_istgt['all_imagesurl']=all_imagesurl
alldata_istgt['all_imageslocation']=all_imageslocation
alldata_istgt['all_adsurl']=all_adsurl
alldata_istgt['all_adsid']=all_adsid
pickle.dump(alldata_istgt,open("alldata_istgtv2.pkl","wb"))

# Get similar images from HBase

# Compute connected components
