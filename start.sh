set -e
. lib.sh

confdir=$rootdir/fluentd/etc/conf.d
conf_gen=$vardir/fluentd/etc/conf_generated.d
export confdir etcdir

for f in `ls $rootdir/fluentd/etc/start.d`  ; do
  fn=$rootdir/fluentd/etc/start.d/$f
  if [ -x $fn ] ; then
     eval $fn
  else
     sh $fn
  fi 
done

if ! [ -d $conf_gen ] ; then
  rm -rf $conf_gen
fi
mkdir -p $conf_gen

with_file() {
  b="${1%%.*}"
  if [ "${b#with_}" = "$b" ] ; then
    return 0
  fi
  eval "[ -n \"\$$b\" ]"
}

SELECT_FILE_HANDLER=with_file
expand_conf $confdir $conf_gen

FLUENTD_CONF=fluent.conf


exec fluentd -c /fluentd/etc/$FLUENTD_CONF -p /fluentd/plugins $FLUENTD_OPT

