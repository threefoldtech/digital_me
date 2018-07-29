from jumpscale import j

p = j.tools.prefab.local
p.runtimes.pip.install("dnslib,nameparser,gevent,unidecode")

j.servers.zdb.test(build=True)

j.data.schema.test()

j.data.bcdb.test()

j.data.types.date.test()
j.data.types.numeric.test()


if p.platformtype.isLinux:
    j.servers.dns.test()