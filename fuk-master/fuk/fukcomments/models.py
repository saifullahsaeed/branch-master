from django.db import models
import datetime
from django.contrib.auth.models import User
from django.contrib.comments.managers import CommentManager
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from django.contrib.comments.models import BaseCommentAbstractModel

class FukComment(BaseCommentAbstractModel):
     """ Subclassing the comment abstract base class, adding user Id field and copying some stuff from the contrib.comment model."""
     user = models.ForeignKey(User, verbose_name=_('user'),
                     blank=True, null=True, related_name="%(class)s_comments")
     comment = models.TextField(_('comment'), max_length=3000)

     # Metadata about the comment
     submit_date = models.DateTimeField(_('date/time submitted'), default=None)
     ip_address  = models.IPAddressField(_('IP address'), blank=True, null=True)
     is_public   = models.BooleanField(_('is public'), default=True,
                     help_text=_('Uncheck this box to make the comment effectively ' \
                                 'disappear from the site.'))
     is_removed  = models.BooleanField(_('is removed'), default=False,
                     help_text=_('Check this box if the comment is inappropriate. ' \
                                 'A "This comment has been removed" message will ' \
                                 'be displayed instead.'))
                                 
     class Meta:
         db_table = "fuk_comments"
         ordering = ('submit_date',)
         permissions = [("can_moderate", "Can moderate comments")]
         verbose_name = _('comment')
         verbose_name_plural = _('comments')

     def __unicode__(self):
         return "%s: %s..." % (self.name, self.comment[:50])

     def save(self, *args, **kwargs):
         if self.submit_date is None:
             self.submit_date = datetime.datetime.now()
         super(FukComment, self).save(*args, **kwargs)

     def _get_userinfo(self):
         """
         Get a dictionary that pulls together information about the poster
         safely for both authenticated and non-authenticated comments.

         This dict will have ``name``, ``email``, and ``url`` fields.
         """
         if not hasattr(self, "_userinfo"):
             u = self.user
             self._userinfo = {
                 "name"  : u.username,
                 "email" : u.email,
                 "url"   : ''
             }
         return self._userinfo
         
     userinfo = property(_get_userinfo, doc=_get_userinfo.__doc__)

     def _get_name(self):
         return self.userinfo["name"]
     def _set_name(self, val):
         if self.user_id:
             raise AttributeError(_("This comment was posted by an authenticated "\
                                    "user and thus the name is read-only."))
         self.user_name = val
     name = property(_get_name, _set_name, doc="The name of the user who posted this comment")

     def _get_email(self):
         return self.userinfo["email"]
     def _set_email(self, val):
         if self.user_id:
             raise AttributeError(_("This comment was posted by an authenticated "\
                                    "user and thus the email is read-only."))
         self.user_email = val
     email = property(_get_email, _set_email, doc="The email of the user who posted this comment")

     def _get_url(self):
         return self.userinfo["url"]
     def _set_url(self, val):
         self.user_url = val
     url = property(_get_url, _set_url, doc="The URL given by the user who posted this comment")

     def get_absolute_url(self, anchor_pattern="#c%(id)s"):
         return self.get_content_object_url() + (anchor_pattern % self.__dict__)

     def get_as_text(self):
         """
         Return this comment as plain text.  Useful for emails.
         """
         d = {
             'user': self.user or self.name,
             'date': self.submit_date,
             'comment': self.comment,
             'domain': self.site.domain,
             'url': self.get_absolute_url()
         }
         return _('Posted by %(user)s at %(date)s\n\n%(comment)s\n\nhttp://%(domain)s%(url)s') % d
                    