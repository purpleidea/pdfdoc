[INSTALL](https://pdfdoc-purpleidea.rhcloud.com/pdf/https://github.com/purpleidea/pdfdoc/blob/master/INSTALL.md)

0. This doc should be updated so that installation is more automatic.

1. Create a new openshift service... This involved me running something like:
<pre>
rhc create-app pdfdoc python-3.3
</pre>

2. Copy the static directory to:
<pre>
$OPENSHIFT_DATA_DIR/static/
</pre>

3. Install pandoc...
I don't know what the elegant way is, so instead I copied all the .so files
that pandoc needs from a CentOS 6.5 installation into:
<pre>
$OPENSHIFT_DATA_DIR/static/pandoc/bin/so/
</pre>
I copied the data directory into:
<pre>
$OPENSHIFT_DATA_DIR/static/pandoc/bin/data/
</pre>
I copied the pandoc binary to:
<pre>
$OPENSHIFT_DATA_DIR/static/pandoc/bin/pandoc.bin
</pre>
I installed a pandoc bash script at:
<pre>
$OPENSHIFT_DATA_DIR/static/pandoc/bin/pandoc
</pre>
It is included in this source repository.
I would have rather installed a single statically compiled pandoc binary, but
it seems to be quite impossible at this time. If you can help with this, please
do:
[https://github.com/jgm/pandoc/issues/11](https://github.com/jgm/pandoc/issues/11)

4. Install latex from the net installer:
[https://www.tug.org/texlive/acquire-netinstall.html](https://www.tug.org/texlive/acquire-netinstall.html)
You'll need to run:
<pre>
./ti-install
</pre>
I used a medium size install, and removed the font doc options... Make sure to
install into:
<pre>
$OPENSHIFT_DATA_DIR/latex/
</pre>

5. git push your code up to openshift, and enjoy!

