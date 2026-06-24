\* Source Pyomo model name=Producao_simples *\

max 
obj:
+40 xA
+30 xB

s.t.

c_u_cap_m1_:
+2 xA
+1 xB
<= 100

c_u_cap_m2_:
+1 xA
+2 xB
<= 80

c_u_dem_A_:
+1 xA
<= 40

c_u_dem_B_:
+1 xB
<= 50

bounds
   0 <= xA <= +inf
   0 <= xB <= +inf
end
