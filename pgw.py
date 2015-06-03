#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
	PGW
	~~~~~~

	Payment gateways VNF with RESTful API.

	:copyright: (c) 2015 by Anton K. Komarov.
	:license: MIT, see LICENSE for more details.
"""

import os
import sqlite3
from flask import Flask, g, abort, jsonify
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from contextlib import closing
import iptc
import dns.resolver

pgw_fields = {
	'domain': fields.String,
	'uri': fields.Url('pgw',absolute=True)
}

app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'pgw.db'),
    INTF_IN='eth1',
    PORTAL_IP='127.0.0.1:80',
    DEBUG=True,
))
app.config.from_envvar('PGW_SETTINGS', silent=True)

def connect_db():
	"""Connects to the specific database."""
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv

def init_db():
	"""Initializes the database."""
	db = get_db()
	with app.open_resource('schema.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()

@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	init_db()
	print('Initialized the database.')

def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()

	return g.sqlite_db

def query_db(query, args=(), one=False):
	"""A query function that combines getting the cursor,
	executing and fetching the results.
	"""
	db=get_db()
	cur = db.execute(query, args)
	rv = cur.fetchall()
	cur.close()
	db.commit()

	return (rv[0] if rv else None) if one else rv

def tbl_prep():
	"""Prepare table NAT and two chains."""
        tblf=iptc.Table(iptc.Table.NAT)
        tblf.flush()

        chain_pr = iptc.Chain(tblf, 'PREROUTING')
        chain_pr.flush()

        chain_pgw = tblf.create_chain('PAYMENT_GW')

        rule = iptc.Rule()
	rule.protocol='udp'
	rule.create_target('ACCEPT')
	m = rule.create_match('udp')
	m.dport='53'
	rule.in_interface=app.config['INTF_IN']
        chain_pr.append_rule(rule)

        rule = iptc.Rule()
        rule.create_target('PAYMENT_GW')
	rule.protocol='tcp'
	rule.in_interface=app.config['INTF_IN']
        chain_pr.append_rule(rule)

	rule = iptc.Rule()
	rule.protocol='tcp'
	rule.in_interface=app.config['INTF_IN']
	t = rule.create_target('DNAT')
	t.to_destination=app.config['PORTAL_IP']
	m = rule.create_match('tcp')
	m.dport='80'
        chain_pr.append_rule(rule)

	rule = iptc.Rule()
	rule.create_target('DROP')
	rule.in_interface=app.config['INTF_IN']
        chain_pr.append_rule(rule)

        return chain_pgw

def query_dns(host_list):
	"""Get host ip mappings from DNS records."""
        collection = {}
        for host in host_list:
		try:
	                res = dns.resolver.query(host['domain'],'A')
                	for a in res:
				collection[a.address]=host['domain']
		except:
			pass	

        return collection

@app.route('/pgw/api/v1.0/pgws/reload')
def reload_pgw():
	"""Reload iptables structure from scratch."""
        pgws=query_db('select domain from pgws order by id')
        chain_pgw=tbl_prep()
        for pgw in pgws:
		append_pgw(pgw[0])
	return jsonify({'result': True}), 202

def append_pgw(pgw):
	"""Append payment gw to iptables chain."""
	chain_pgw = iptc.Chain(iptc.Table(iptc.Table.NAT),'PAYMENT_GW')
	if not iptc.Table(iptc.Table.NAT).is_chain(chain_pgw):
		tbl_prep()
	collection=query_dns([{'domain':pgw},])
	for ip,host in collection.items():
		rule = iptc.Rule()
		rule.create_target('ACCEPT')
		m = rule.create_match('comment')
		m.comment=str(host)
		rule.dst=str(ip)
		chain_pgw.append_rule(rule)
	return len(collection)

def delete_pgw(pgw):
	""" Delete payment gw from iptables chain."""
	chain_pgw = iptc.Chain(iptc.Table(iptc.Table.NAT),'PAYMENT_GW')
	if not iptc.Table(iptc.Table.NAT).is_chain(chain_pgw):
		tbl_prep()
		return
	for r in chain_pgw.rules:
	   for m in r.matches:
	      if 'comment' in m.parameters:
		 if m.parameters['comment']==pgw:
		    chain_pgw.delete_rule(r)

@app.teardown_appcontext
def close_db(error):
 	"""Closes the database again at the end of the request."""
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

class PgwListAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('domain', type=str, required=True,
                                   help='No domain provided',
                                   location='json')
        super(PgwListAPI, self).__init__()

    def get(self):
	pgws=query_db('select id, domain from pgws order by id desc')
        return {'pgws': [marshal(pgw, pgw_fields) for pgw in pgws]}

    def post(self):
        args = self.reqparse.parse_args()
	pgws=query_db('select id, domain from pgws where domain=?', [args['domain'],])
	if len(pgws)==0:
		if (append_pgw(args['domain'])>0):
			query_db('insert into pgws (domain) values (?)', [args['domain'],])
	pgws = query_db('select id, domain from pgws order by id desc')

        return {'pgws': [marshal(pgw, pgw_fields) for pgw in pgws]}, 201

class PgwAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('domain', type=str, location='json')
        super(PgwAPI, self).__init__()

    def get(self, id):
	pgw = query_db('select id, domain from pgws where id=?', [id,])
        if len(pgw) == 0:
            abort(404)
        return {'pgw': marshal(pgw[0], pgw_fields)}

    def delete(self, id):
	pgw=query_db('select domain from pgws where id=?', [id,])
	delete_pgw(str(pgw[0][0]))
	query_db('delete from pgws where id=?', [id,])

        return {'result': True}

api.add_resource(PgwListAPI, '/pgw/api/v1.0/pgws', endpoint='pgws')
api.add_resource(PgwAPI, '/pgw/api/v1.0/pgws/<int:id>', endpoint='pgw')

if __name__ == '__main__':
    	app.run()
