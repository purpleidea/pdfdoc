#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pdfdoc - PDF as a service
# Copyright (C) 2014+ James Shubin
# Written by James Shubin <james@shubin.ca>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# XXX: parse user input for safety and escape it... somewhere...

import os
import shutil
import logging	# FIXME: logging doesn't seem to log to the openshift logs!
import urllib.request

#home = os.getenv('OPENSHIFT_HOMEDIR')
data = os.getenv('OPENSHIFT_DATA_DIR')
if data is not None:
	l = os.path.join(data, 'latex/bin/x86_64-linux/')
	p = os.path.join(data, 'pandoc/bin/')
	os.environ['PATH'] = ':'.join([l, p, os.environ['PATH']])

import pypandoc

def github_tokens_to_dictionary(tokens):
	"""Split an array of tokens into a named dictionary."""
	variables = ['site', 'username', 'project', 'commit', 'filename']
	site = 'github.com'

	if len(tokens) == 5:
		(username, project, t, commit, filename) = tokens
	elif len(tokens) == 4:
		(username, project, commit, filename) = tokens
	else:
		return False

	# TODO: parse off any ?foo=bar from the filename

	l = locals()	# needed because locals() doesn't work in a dict compr.
	return {k: l[k] for k in variables}

def github_dict_to_url(dictionary):
	"""Return a download URL from the dictionary of essential variables."""
	return ("https://github.com/%(username)s/%(project)s/raw/%(commit)s/%(filename)s" % dictionary)

def github_file_location(dictionary, type=None, mkdir=True):
	"""Return the location of where we'll store the file on disk."""

	name = os.getenv('OPENSHIFT_APP_NAME')
	if name is None: name = 'openshift'

	tmp = os.getenv('OPENSHIFT_TMP_DIR')
	if tmp is None: tmp = '/tmp/'

	filename, ext = os.path.splitext(dictionary['filename'])
	if type is None:
		pass
	elif type.startswith('.'): ext = str(type)
	else:
		ext = '.'+str(type)

	# TODO: validate valid extensions

	path = os.path.join(
		tmp,
		name,
		"%(site)s/%(username)s/%(project)s/%(commit)s/" % dictionary,
		"%s%s" % (filename, ext)
	)

	if mkdir: logging.debug("mkdir -p: %s" % os.path.dirname(path))
	if mkdir: os.makedirs(os.path.dirname(path), exist_ok=True)

	return path

def download_file(dictionary):

	url = github_dict_to_url(dictionary)
	filename = github_file_location(dictionary)
	# r is response, o is output

	# TODO: error gracefully and report the reason on missing file

	with urllib.request.urlopen(url) as r, open(filename, 'wb') as output:
		shutil.copyfileobj(r, output)
		output.flush()
		os.fsync(output.fileno())
		output.close()

	# FIXME: return error ?
	return True

def convert_to_pdf(dictionary):

	f = github_file_location(dictionary)
	pdf = github_file_location(dictionary, type='pdf')

	import time; time.sleep(1)
	# FIXME: replace with something safer, without a shell...
	x = os.system("pandoc '%s' -o '%s'" % (f, pdf))
	if x != 0:
		return False

	return True

def send_file(filename, environ, start_response, ctype=None, block_size=1024):
	"""Send a file to the user. The return value must be returned by the
	application() function."""
	try:
		f = open(filename, 'rb')
	except IOError:
		start_response('404 Not Found', [('Content-type', 'text/plain')])
		return ['Page not found']
	b = os.path.basename(filename)
	size = os.path.getsize(filename)
	if ctype is None:
		ext = os.path.splitext(filename)[1]
		if ext == '.css':
			ctype = 'text/css'
		else:
			ctype = 'text/plain'
	start_response('200 OK',
		[
			('Content-Type', ctype),
			('Content-length', str(size)),
			# TODO: override this filename from the querystring ?f=
			('Content-Disposition', "attachment; filename=%s" % b)
		]
	)
	# return the entire file as per:
	# http://legacy.python.org/dev/peps/pep-0333/#optional-platform-specific-file-handling
	if 'wsgi.file_wrapper' in environ:
		return environ['wsgi.file_wrapper'](f, block_size)
	else:
		return iter(lambda: f.read(block_size), '')

# FIXME: cache downloads for known-things... eg specific commits... check file mtime for master commit (since it changes)

def file_uptodate(dictionary):
	"""Returns True if the file does not need to be refreshed."""

	# FIXME: look at existence and mtimes...
	return False

def run(tokens, environ, start_response):

	dictionary = github_tokens_to_dictionary(tokens)
	if not dictionary:
		return False

	if not file_uptodate(dictionary):
		result = download_file(dictionary)
		if not result:
			return False

	result = convert_to_pdf(dictionary)
	if not result:
		return False

	pdf = github_file_location(dictionary, type='pdf')
	return send_file(filename=pdf, environ=environ, start_response=start_response, ctype='application/pdf')

def application(environ, start_response):

	error = None
	if environ['PATH_INFO'] == '/health':
		response_body = '1'
		ctype = 'text/plain'
		status = '200 OK'
		response_headers = [('Content-Type', ctype), ('Content-Length', str(len(response_body)))]
		start_response(status, response_headers)
		return [response_body.encode('utf-8')]

	#elif environ['PATH_INFO'] == '/env':
	#	response_body = ['%s: %s' % (key, value) for key, value in sorted(environ.items())]
	#	response_body = '\n'.join(response_body)
	elif environ['PATH_INFO'].startswith('/static/'):

		data = os.getenv('OPENSHIFT_DATA_DIR')
		filename = os.path.join(data, environ['PATH_INFO'][1:])
		return send_file(filename, environ, start_response, block_size=1024)

	elif environ['PATH_INFO'].startswith('/pdf/'):
		tokens = environ['PATH_INFO'].split('/')
		# TODO: make this parsing not gross :P
		if tokens[0] == '': tokens.pop(0)
		if tokens[-1] == '': tokens.pop()
		assert tokens[0] == 'pdf'; tokens.pop(0)
		if len(tokens) > 0:
			if tokens[0] == 'https:': tokens.pop(0)
			elif tokens[0] == 'http:': tokens.pop(0)

		if len(tokens) > 0 and tokens[0] == 'github.com':
			tokens.pop(0)

			logging.info('hello from @purpleidea');

			result = run(tokens, environ=environ, start_response=start_response)

			if result:
				return result
			else:
				# fail
				error = 'Error processing URL :('
		else:
			error = 'Invalid URL specified!'

	if error is None: error_msg = ''
	else: error_msg = ('<div class="alert alert-danger" role="alert"><span class="glyphicon glyphicon-exclamation-sign"></span>&nbsp;%(error)s</div>' % {'error': error})
	ctype = 'text/html'
	response_body = """<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<meta name="description" content="">
		<meta name="author" content="James Shubin">
		<link rel="icon" href="/static/favicon.ico">

		<title>Welcome to %(title)s</title>

		<!-- Bootstrap core CSS -->
		<link href="/static/dist/css/bootstrap.min.css" rel="stylesheet">

		<!-- Custom styles for this template -->
		<link href="/static/jumbotron-narrow.css" rel="stylesheet">

		<!-- HTML5 shim and Respond.js IE8 support of HTML5 elements and media queries -->
		<!--[if lt IE 9]>
			<script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
			<script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
		<![endif]-->
	<script language="javascript">
		document.addEventListener(
			"keydown",
			function( e ) {
				var keyCode = e.keyCode || e.which;
				if ( keyCode === 13 ) { // enter pressed
					window.location.assign('/pdf/'+document.getElementById('url').value);
				}
			},
			false
		);
	</script>
	</head>

	<body>

		<div class="container">
			<div class="header">
				<ul class="nav nav-pills pull-right">
					<li class="active"><a href="%(home)s">Home</a></li>
					<li><a href="https://github.com/purpleidea/pdfdoc/">About</a></li>
					<li><a href="https://ttboj.wordpress.com/contact/">Contact</a></li>
				</ul>
				<h3 class="text-muted">%(title)s</h3>
			</div>

			<div class="jumbotron">
				<h1>PDF as a service</h1>
				<p class="lead">Enter the URL of your markdown documentation</p>
				<!-- error -->%(error)s
				<p>

					<div class="input-group input-group-lg">
						<span class="input-group-addon">github.com url</span>
						<input type="text" class="form-control" placeholder="url" name="url" id="url">
						<span class="input-group-btn">
							<button class="btn btn-lg btn-success" type="button" onclick="javascript:window.location.assign('/pdf/'+document.getElementById('url').value);">Generate!</button>
						</span>
					</div>
				</p>
			</div>

			<div class="row marketing">
				<div class="col-lg-6">
					<h4><a href="https://github.com/purpleidea/puppet-gluster/commit/a4bf5cad81ca66212f4c8e52edb2e816b8895690">Avoid storing your pdf's in git!</a></h4>
					<p>Leave the binary bits out of this.</p>

					<h4>Document conversion by <a href="https://github.com/jgm/pandoc/">Pandoc</a></h4>
					<p>The LaTeX backend gets it perfect!</p>

					<h4><a href="https://www.gnu.org/philosophy/free-sw.html">Free</a> and <a href="https://www.gnu.org/philosophy/open-source-misses-the-point.html">Open Source</a></h4>
					<p>Free as in freedom, free as in beer.</p>
				</div>

				<div class="col-lg-6">
					<h4><a href="https://pdfdoc-purpleidea.rhcloud.com/pdf/https://github.com/purpleidea/puppet-ipa/blob/master/DOCUMENTATION.md">Generate beautiful documentation!</a></h4>
					<p>The best quality document conversion available.</p>

					<h4>Written in <a href="https://www.python.org/">Python</a></h4>
					<p>Not as trendy as some of the less mature languages, but still awesome to work with.</p>

					<h4>Powered by <a href="https://www.openshift.com/">Openshift</a></h4>
					<p>You'll never get locked-in to this [self-]hosted PaaS!</p>
				</div>
			</div>

			<div class="footer">
				<p>&copy; <a href="https://twitter.com/#!/purpleidea">James Shubin</a> 2014</p>
			</div>

		</div> <!-- /container -->

		<!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
		<script src="/static/assets/js/ie10-viewport-bug-workaround.js"></script>
		<a href="https://github.com/purpleidea"><img style="position: absolute; top: 0; right: 0; border: 0;" src="https://camo.githubusercontent.com/38ef81f8aca64bb9a64448d0d70f1308ef5341ab/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f6769746875622f726962626f6e732f666f726b6d655f72696768745f6461726b626c75655f3132313632312e706e67" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_darkblue_121621.png"></a>
	</body>
</html>
""" % {
	'title': os.getenv('OPENSHIFT_APP_NAME'),
	'home': 'https://' + os.getenv('OPENSHIFT_APP_DNS'),
	'error': error_msg,
}

	status = '200 OK'
	response_headers = [('Content-Type', ctype), ('Content-Length', str(len(response_body)))]
	start_response(status, response_headers)
	return [response_body.encode('utf-8')]

# local testing
# TODO: this script needs patching so that this will fully work :)
if __name__ == '__main__':
	from wsgiref.simple_server import make_server
	httpd = make_server('localhost', 8051, application)
	print('xdg-open http://localhost:8051')
	# wait for a single request, serve it and quit
	httpd.handle_request()
