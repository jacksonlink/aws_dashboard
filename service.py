from flask import Flask, flash, abort, redirect, url_for, request, render_template, make_response, json, Response
import os, sys
import config
import boto.ec2.elb

import re
from boto.ec2 import *


app = Flask(__name__)

@app.route('/')
def index():

	list = []
	creds = config.get_ec2_conf()
	for region in config.region_list():
		conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
		reservations = conn.get_all_reservations()

		for i in range(0, len(reservations)):
			try:
				metadata = reservations[i].instances[0]
				name = re.sub(r'{u\'Name\': u\'', "", str(metadata.tags))
				metadata_name = str(re.sub(r'\'}', "", name))
				metadata_server_id = str(metadata.id)
				metadata_instance_type = str(metadata.instance_type)
				metadata_instance_state = str(metadata.state)
			except:
				metadata_name = ""
				metadata_server_id = ""
				metadata_instance_type = ""
				metadata_instance_state = ""

			list.append({ 
				'name' : metadata_name,
				'server_id' : metadata_server_id,
				'instance_type' : metadata_instance_type,
				'instance_state' : metadata_instance_state,
				'instance_region' : region
			})
	return render_template('index.html',list=list)

@app.route('/volumes/')
def volumes():
	creds = config.get_ec2_conf()
	for region in config.region_list():
		conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
		volumes = conn.get_all_volumes()
		volume_list = []
		for volume in volumes:
			name = re.sub(r'{u\'Name\': u\'', "", str(volume.tags))
			name = str(re.sub(r'\'}', "", name))	
			volume_info = { 'name' : name,
							'id' : volume.id, 
							'size' : volume.size, 
							'status' : volume.status, 
							'type' : volume.type, 
							'attachment_state' : volume.attach_data.instance_id,
							'volume_region' : region }
			volume_list.append(volume_info)

	return render_template('volumes.html',volume_list=volume_list)

@app.route('/stop_instance/<instance_id>/')
def stop_instance(instance_id=None):
	creds = config.get_ec2_conf()
	for region in config.region_list():
		conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
		try:
			conn.stop_instances(instance_ids=[instance_id])
		except:
			print "The instance " + str(instance_id) + " is not in this region.Checking next region " + str(region)
	return index()

@app.route('/start_instance/<instance_id>/')
def start_instance(instance_id=None):
	creds = config.get_ec2_conf()
	for region in config.region_list():
		conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
		try:
			instances = conn.get_only_instances(instance_ids=[instance_id])
			instances[0].start()
		except:
			print "The instance " + str(instance_id) + " is not in this region. Checking next region " + str(region)
	return index()

@app.route('/delete_volume/<volume_id>')
def delete_volume(volume_id=None):
	creds = config.get_ec2_conf()
	for region in config.region_list():
		conn = connect_to_region(region, aws_access_key_id=creds['AWS_ACCESS_KEY_ID'], aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'])
		volume_id = volume_id.encode('ascii')
		try:
			vololume_ids = conn.get_all_volumes(volume_ids=volume_id)
			for volume in vololume_ids:
    				volume.delete()
		except:
			print "The volume " + str(volume_id) + " is not in this region. Checking next region " + str(region)
	return volumes()
		
if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')
