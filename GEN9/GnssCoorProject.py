from turtle import right
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import NamedTuple
from GnssTime import GnssTime

class Bessel1841(NamedTuple):
    a = 6377397.155 # je hlavná polos elipsoidu
    f = 1/(299.1528154) # je geometrické sploštenie elipsoidu
    b = a*(1 - f) # je vedľajšia polos elipsoidu
    e = np.sqrt((a**2 - b**2) / a**2) # je prvá excentricita

class Grs80(NamedTuple):
    a = 6378137.000 # je hlavná polos elipsoidu
    f = 1/(298.257222101) # je geometrické sploštenie elipsoidu
    b = a*(1 - f) # je vedľajšia polos elipsoidu
    e = np.sqrt((a**2 - b**2) / a**2) # je prvá excentricita

class Krovak(NamedTuple):
    a_Bessel1841 = 6377397.155 # dĺžka hlavnej polosi elipsoidu Bessel 1841
    b_Bessel1841 = 6356078.9633 # dĺžka vedľajšej polosi elipsoidu Bessel 1841
    e = np.sqrt((a_Bessel1841**2 - b_Bessel1841**2) / a_Bessel1841**2)
    lamFG = np.radians(17+2/3) # zemepisná dĺžka medzi základnými poludníkmi Ferro a Greenwich na elipsoide Bessel 1841 (Ferro je na západ od Greenwich)
    phi0 = np.radians(49.5) # zemepisná šírka neskreslenej rovnobežky na elipsoide Bessel 1841
    lamKP = np.radians(42.5) # zemepisná dĺžka kartografického pólu na elipsoide Bessel 1841 (definovaná na východ od základného poludníka Ferro)
    alpha = 1.000597498372 # parameter charakterizujúci konformné zobrazenie elipsoidu Bessel 1841 na guľovú plochu (Gaussovu guľu)
    k = 1.003419164 # parameter charakterizujúci konformné zobrazenie elipsoidu Bessel 1841 na guľovú plochu (Gaussovu guľu)
    kc = 0.9999 # koeficient zmenšenia guľovej plochy (Gaussovej gule)
    a = np.radians(30+17/60+17.30311/3600)  # pólová vzdialenosť kartografického pólu na guľovej ploche (Gaussovej guli)
    S0 = np.radians(78.5) # zemepisná šírka základnej kartografickej rovnobežky na guľovej ploche (Gaussovej guli)
    ff = np.radians(45) # pomocna konstanta

class GnssCoorProject(object):
    @staticmethod
    def plh_xyz(plh, elipsoid):
        """ 2.1 Prevod elipsoidických geodetických súradníc phi, lambda, h na pravouhlé karteziánske súradnice XYZ
            Transforms the phi, lambda, height coordinates to X, Y, Z.
            Elipsoid parameter defines the elipsoid with 2 properties - a and f."""
        phi, lam, hei = plh
        N = elipsoid.a/np.sqrt(1 - elipsoid.e**2 * (np.sin(phi)**2))
        X = (N+hei)*np.cos(phi)*np.cos(lam)
        Y = (N+hei)*np.cos(phi)*np.sin(lam)
        Z = (N*(1-elipsoid.e**2)+hei)*np.sin(phi)
        return X, Y, Z

    @staticmethod
    def xyz_plh(xyz, elipsoid):
        """ 2.2 Prevod pravouhlých karteziánskych súradníc XYZ na elipsoidické súradnice phi, lambda, h
            Transforms the X, Y, Z coordinates to phi, lambda, height.
            Elipsoid parameter defines the elipsoid with 2 properties - a and f."""
        X, Y, Z = xyz
        lam = np.arctan(Y/X)
        phi = np.arctan(Z/np.sqrt(X**2+Y**2)*(1/(1-elipsoid.e**2)))
        diff = 1
        while diff > 10E-12:
            N = elipsoid.a / np.sqrt(1 - elipsoid.e**2 * (np.sin(phi)**2))
            h = np.sqrt(X**2 + Y**2)/np.cos(phi) - N
            phi1 = np.arctan(Z/np.sqrt(X**2+Y**2) * ((N+h)/(N+h - elipsoid.e**2*N)))
            diff = abs(phi-phi1)
            phi = phi1

        return phi, lam, h

    @staticmethod
    def gnss_eceftowgs(xyz):
        wgs = list(GnssCoorProject.xyz_plh(xyz, Grs80))
        wgs[0] = np.degrees(wgs[0])
        wgs[1] = np.degrees(wgs[1])
        return wgs

    @staticmethod
    def gnss_toxyz(plh):
        return GnssCoorProject.plh_xyz(plh, Grs80)

    @staticmethod
    def sat_elevation(userecef, satecef):
        dsat = np.linalg.norm(satecef)
        dusr = np.linalg.norm(userecef)
        dusrsat = np.linalg.norm(np.array(satecef)-np.array(userecef))
        return np.arccos((dsat**2 - dusr**2 - dusrsat**2)/(2*dusr*dusrsat))-np.pi/2

    @staticmethod
    def querypoint_ataltitude(userecef, satecef, altitude):
        elev = GnssCoorProject.sat_elevation(userecef, satecef)
        dusr = np.linalg.norm(userecef)
        dist = np.roots([1.0, 2*dusr*np.cos(elev+np.pi/4), dusr**2-(dusr-altitude)**2])
        dist = np.absolute(dist[0])

        npuecef = np.array(userecef)
        iovector = np.array(satecef) - npuecef
        ioecef = npuecef + dist/np.linalg.norm(iovector) * (iovector)
        return ioecef
