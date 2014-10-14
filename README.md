# *pdfdoc*: PDF as a service

This is an openshift web service for generating a pdf from markdown.
Simply append the GitHub file URL to:

<pre>https://pdfdoc-purpleidea.rhcloud.com/pdf/</pre>

and you'll get sent a PDF of the markdown document. For example, to get a PDF
of this README, you can go to:
[https://pdfdoc-purpleidea.rhcloud.com/pdf/https://github.com/purpleidea/pdfdoc/blob/master/README.md](https://pdfdoc-purpleidea.rhcloud.com/pdf/https://github.com/purpleidea/pdfdoc/blob/master/README.md)

## Installation:
Please read the [INSTALL](INSTALL.md) file for instructions on getting this
installed.

## Notes:
This was built because existing PDF generators make ugly documents! Only pandoc
seems to make good looking ones. I looked at gitprint, and phantomjs, but the
output is terrible! I also wanted an excuse to hack on an openshift app.

## FAQ:
(Send your questions as a patch to this FAQ! I'll review it, merge it, and
respond by commit with the answer.)

### Why is this called pdfdoc?
This started out as mdpdf, as in markdown-to-pdf.
As we all know, an MD is a doctor, so it became pdf doctor.
This name didn't make much sense, so it was then named pdfdoc.
This makes a whole lot of sense because it makes pdfs for documentation!

### Why doesn't this project have a cool logo?
Because I'm a terrible graphic designer! Please feel free to send me one for
the project. Thanks in advance!

### The web front end you put together is awful, why is it so bad?
As mentioned above, I started this project to scratch an itch, and to try out
openshift. My web frontend and bootstrap skills are surely terrible! Please
feel free to send in patches!

### There are terrible issues with the backend!
Once again, I wrote this as a quick POC hack, and to scratch an itch. Please
voice your complains in the form of constructive patches :)

### Is the code as bad as the FAQ makes it seem?
I don't think so, but there is room for improvement, and it's more interesting
if you I address all the haters up front :)

## Patches:
Send me your patches! Yup. Do it :)

##

Happy hacking!

