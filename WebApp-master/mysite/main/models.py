from django.db import models


# ComputerPart is a table in the DB. We define everything about it here.
# right now, we have only defined the fields that it has
class ComputerPart(models.Model):
    # the following define the fields for this table
    # models.* is the type of field it is. For example, models.CharField is a string, basically.

    # AutoField assigns a number from 1 - N to each part. Useful as a primary key.
    partID = models.AutoField(primary_key=True)
    title = models.CharField(max_length=300)

    # a URLField is just a special CharField. I don't know what the difference is, but it works.
    url = models.URLField(max_length=600)

    # TODO: price is saved as a string because either our ebay or cl search gives price as a string.
    #   if we want to do any math with price, it's probably gotta be a DecimalField. We need to figure out where
    #   price is being reported as a string, convert it to a number, and change this field to a numeric field.
    price = models.CharField(max_length=300)
    # website != url. it's just a string where we can say what website the part came from.
    website = models.CharField(max_length=300)
    pictureUrl = models.URLField(max_length=600, null=True, blank=True)
    location = models.CharField(max_length=300, null=True, blank=True)


class CPUs(models.Model):
    partID = models.AutoField(primary_key=True)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class GraphicsCards(models.Model):
    partID = models.AutoField(primary_key=True)
    chipsetManufacturer = models.CharField(max_length=100)
    #  cardManufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class HDDs(models.Model):
    partID = models.AutoField(primary_key=True)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    size = models.DecimalField(max_digits=15, decimal_places=0)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class SSDs(models.Model):
    partID = models.AutoField(primary_key=True)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    size = models.DecimalField(max_digits=15, decimal_places=0)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class RAM(models.Model):
    partID = models.AutoField(primary_key=True)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    size = models.DecimalField(max_digits=15, decimal_places=0)
    memorySplit = models.CharField(max_length=4)
    frequency = models.DecimalField(max_digits=4, decimal_places=0)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class Motherboards(models.Model):
    partID = models.AutoField(primary_key=True)
    socketID = models.DecimalField(max_digits=10, decimal_places=0)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class airCoolers(models.Model):
    partID = models.AutoField(primary_key=True)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class waterCoolers(models.Model):
    partID = models.AutoField(primary_key=True)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class powerSupplies(models.Model):
    partID = models.AutoField(primary_key=True)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    wattage = models.DecimalField(max_digits=4, decimal_places=0)
    count = models.DecimalField(max_digits=10, decimal_places=0)
    dailyTotalPrice = models.DecimalField(max_digits=10, decimal_places=2)


class HistoricalTracking(models.Model):
    date = models.DateField(primary_key=True)
    partID_0 = models.CharField(max_length=300)
    partID_1 = models.CharField(max_length=300)
    partID_2 = models.CharField(max_length=300)
    partID_3 = models.CharField(max_length=300)
    partID_4 = models.CharField(max_length=300)
    partID_5 = models.CharField(max_length=300)
    partID_6 = models.CharField(max_length=300)
    partID_7 = models.CharField(max_length=300)
    partID_8 = models.CharField(max_length=300)
    partID_9 = models.CharField(max_length=300)
    partID_10 = models.CharField(max_length=300)
    partID_11 = models.CharField(max_length=300)
    partID_12 = models.CharField(max_length=300)
    partID_13 = models.CharField(max_length=300)
    partID_14 = models.CharField(max_length=300)
    partID_15 = models.CharField(max_length=300)
    partID_16 = models.CharField(max_length=300)
    partID_17 = models.CharField(max_length=300)
    partID_18 = models.CharField(max_length=300)
    partID_19 = models.CharField(max_length=300)
    partID_20 = models.CharField(max_length=300)
    partID_21 = models.CharField(max_length=300)
    partID_22 = models.CharField(max_length=300)
    partID_23 = models.CharField(max_length=300)
    partID_24 = models.CharField(max_length=300)
    partID_25 = models.CharField(max_length=300)
    partID_26 = models.CharField(max_length=300)
    partID_27 = models.CharField(max_length=300)
    partID_28 = models.CharField(max_length=300)
    partID_29 = models.CharField(max_length=300)
    partID_30 = models.CharField(max_length=300)
    partID_31 = models.CharField(max_length=300)
    partID_32 = models.CharField(max_length=300)
    partID_33 = models.CharField(max_length=300)
    partID_34 = models.CharField(max_length=300)
    partID_35 = models.CharField(max_length=300)
    partID_36 = models.CharField(max_length=300)
    partID_37 = models.CharField(max_length=300)
    partID_38 = models.CharField(max_length=300)
    partID_39 = models.CharField(max_length=300)
    partID_40 = models.CharField(max_length=300)
    partID_41 = models.CharField(max_length=300)
    partID_42 = models.CharField(max_length=300)
    partID_43 = models.CharField(max_length=300)
    partID_44 = models.CharField(max_length=300)
    partID_45 = models.CharField(max_length=300)
    partID_46 = models.CharField(max_length=300)
    partID_47 = models.CharField(max_length=300)
    partID_48 = models.CharField(max_length=300)
    partID_49 = models.CharField(max_length=300)
    partID_50 = models.CharField(max_length=300)
    partID_51 = models.CharField(max_length=300)
    partID_52 = models.CharField(max_length=300)
    partID_53 = models.CharField(max_length=300)
    partID_54 = models.CharField(max_length=300)
    partID_55 = models.CharField(max_length=300)
    partID_56 = models.CharField(max_length=300)
    partID_57 = models.CharField(max_length=300)
    partID_58 = models.CharField(max_length=300)
    partID_59 = models.CharField(max_length=300)
    partID_60 = models.CharField(max_length=300)
    partID_61 = models.CharField(max_length=300)
    partID_62 = models.CharField(max_length=300)
    partID_63 = models.CharField(max_length=300)
    partID_64 = models.CharField(max_length=300)
    partID_65 = models.CharField(max_length=300)
    partID_66 = models.CharField(max_length=300)
    partID_67 = models.CharField(max_length=300)
    partID_68 = models.CharField(max_length=300)
    partID_69 = models.CharField(max_length=300)
    partID_70 = models.CharField(max_length=300)
    partID_71 = models.CharField(max_length=300)
    partID_72 = models.CharField(max_length=300)
    partID_73 = models.CharField(max_length=300)
    partID_74 = models.CharField(max_length=300)
    partID_75 = models.CharField(max_length=300)
    partID_76 = models.CharField(max_length=300)
    partID_77 = models.CharField(max_length=300)
    partID_78 = models.CharField(max_length=300)
    partID_79 = models.CharField(max_length=300)
    partID_80 = models.CharField(max_length=300)
    partID_81 = models.CharField(max_length=300)
    partID_82 = models.CharField(max_length=300)
    partID_83 = models.CharField(max_length=300)
    partID_84 = models.CharField(max_length=300)
    partID_85 = models.CharField(max_length=300)
    partID_86 = models.CharField(max_length=300)
    partID_87 = models.CharField(max_length=300)
    partID_88 = models.CharField(max_length=300)
    partID_89 = models.CharField(max_length=300)
    partID_90 = models.CharField(max_length=300)
    partID_91 = models.CharField(max_length=300)
    partID_92 = models.CharField(max_length=300)
    partID_93 = models.CharField(max_length=300)
    partID_94 = models.CharField(max_length=300)
    partID_95 = models.CharField(max_length=300)
    partID_96 = models.CharField(max_length=300)
    partID_97 = models.CharField(max_length=300)
    partID_98 = models.CharField(max_length=300)
    partID_99 = models.CharField(max_length=300)
    partID_100 = models.CharField(max_length=300)
    partID_101 = models.CharField(max_length=300)
    partID_102 = models.CharField(max_length=300)
    partID_103 = models.CharField(max_length=300)
    partID_104 = models.CharField(max_length=300)
    partID_105 = models.CharField(max_length=300)
    partID_106 = models.CharField(max_length=300)
    partID_107 = models.CharField(max_length=300)
    partID_108 = models.CharField(max_length=300)
    partID_109 = models.CharField(max_length=300)
    partID_110 = models.CharField(max_length=300)
    partID_111 = models.CharField(max_length=300)
    partID_112 = models.CharField(max_length=300)
    partID_113 = models.CharField(max_length=300)
    partID_114 = models.CharField(max_length=300)
    partID_115 = models.CharField(max_length=300)
    partID_116 = models.CharField(max_length=300)
    partID_117 = models.CharField(max_length=300)
    partID_118 = models.CharField(max_length=300)
    partID_119 = models.CharField(max_length=300)
    partID_120 = models.CharField(max_length=300)
    partID_121 = models.CharField(max_length=300)
    partID_122 = models.CharField(max_length=300)
    partID_123 = models.CharField(max_length=300)
    partID_124 = models.CharField(max_length=300)
    partID_125 = models.CharField(max_length=300)
    partID_126 = models.CharField(max_length=300)
    partID_127 = models.CharField(max_length=300)
    partID_128 = models.CharField(max_length=300)
    partID_129 = models.CharField(max_length=300)


class PartList(models.Model):
    partID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
