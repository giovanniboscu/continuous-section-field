# CLI examples: tapered same-family sections

These examples use the same section family for `S0` and `S1`, with different dimensions.


>sp_csf
>
>is alias of
>
>python3 -m csf.utils.sp_csf


Recommended mode:

```bash
--morph-mode native
```

because the native `sectionproperties` vertex order is preserved.

Each command also includes:

```bash
--gen-actions
```

to generate the companion CSF actions YAML file.

## 1. Tapered rectangular hollow section

```bash
python3 -m csf.utils.sp_csf rectangular_hollow_section \
  --s0 d=300,b=200,t=12,r_out=20,n_r=8,z=0 \
  --s1 d=200,b=150,t=8,r_out=15,n_r=8,z=10 \
  --name=rhs \
  --out=tapered_rhs.yaml \
  --morph-mode native \
  --gen-actions
```

## 2. Tapered circular hollow section

```bash
python3 -m csf.utils.sp_csf circular_hollow_section \
  --s0 d=300,t=12,n=96,z=0 \
  --s1 d=180,t=8,n=96,z=10 \
  --name=chs \
  --out=tapered_chs.yaml \
  --morph-mode native \
  --gen-actions
```

## 3. Tapered I-section

```bash
python3 -m csf.utils.sp_csf i_section \
  --s0 d=300,b=150,t_f=15,t_w=10,r=15,n_r=8,z=0 \
  --s1 d=220,b=120,t_f=10,t_w=7,r=10,n_r=8,z=10 \
  --name=ibeam \
  --out=tapered_i_section.yaml \
  --morph-mode native \
  --gen-actions
```

## 4. Tapered channel section

```bash
python3 -m csf.utils.sp_csf channel_section \
  --s0 d=300,b=120,t_f=15,t_w=10,r=12,n_r=8,z=0 \
  --s1 d=220,b=90,t_f=10,t_w=7,r=8,n_r=8,z=10 \
  --name=channel \
  --out=tapered_channel.yaml \
  --morph-mode native \
  --gen-actions
```

## 5. Tapered rectangular solid section

```bash
python3 -m csf.utils.sp_csf rectangular_section \
  --s0 d=300,b=150,z=0 \
  --s1 d=200,b=100,z=10 \
  --name=rect \
  --out=tapered_rectangular.yaml \
  --morph-mode native \
  --gen-actions
```
---

`sectionproperties` is used as the analysis backend for the generated/interpolated sections. 
Please refer to the original project and its license:
https://github.com/robbievanleeuwen/section-properties

