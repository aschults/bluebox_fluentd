set -e
. lib.sh

confbase=$rootdir/fluentd/etc
confdir=$rootdir/fluentd/etc/conf.d
confdir2=$rootdir/fluentd/etc/conf_custom.d
conf_gen=$vardir/fluentd/etc/conf_generated.d
conf_gen2=$vardir/fluentd/etc/conf_custom_generated.d
export confdir etcdir confbase confdir2 conf_gen2

for f in `ls $rootdir/fluentd/etc/start.d`  ; do
  fn=$rootdir/fluentd/etc/start.d/$f
  if [ -x $fn ] ; then
     eval $fn
  else
     sh $fn
  fi 
done


with_file() {
  b="${1%%.*}"
  if [ "${b#with_}" = "$b" ] ; then
    return 0
  fi
  eval "[ -n \"\$$b\" ]"
}

if ! [ -d $conf_gen ] ; then
  rm -rf $conf_gen
fi
mkdir -p $conf_gen

if ! [ -d $conf_gen2 ] ; then
  rm -rf $conf_gen2
fi
mkdir -p $conf_gen2

SELECT_FILE_HANDLER=
expand_conf $confdir2 $conf_gen2

SELECT_FILE_HANDLER=with_file
expand_conf $confdir $conf_gen

FLUENTD_CONF=fluent.conf


exec fluentd -c /fluentd/etc/$FLUENTD_CONF -p /fluentd/plugins $FLUENTD_OPT

