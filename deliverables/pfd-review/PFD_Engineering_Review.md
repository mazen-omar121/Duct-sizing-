# Engineering review: N-19082-RO-012-TQT-AES-PFD-B3-001 to005 Rev0

Review of all five supplied Rev0 PFD sheets and the two engineer comments in the user message, dated 13 October 2026 (Dubai). Evidence is the visible drawing and extracted labels, checked at full-page and enlarged detail scales. The referenced TAQA specifications/P&IDs, vendor data and hydraulic/transient calculations were not supplied. Not shown means absent from this PFD, not proof that the eventual installation or vendor package omits the device. Major flow paths, interface functions and isolation topology should be resolved on the PFD; detailed valve types, sizes, classes, settings and minor vents/drains require P&ID/vendor confirmation. High means resolve the operating/safety/availability function before design closeout; Medium means clarify or close through detailed design; Low means drawing consistency. This is a review record, not an approved design or a revised process drawing.

**Disposition: revise the identified functional arrangements and reconcile with P&IDs before technical closeout.**

## What the drawing already includes

- Normal water path is coherent: incoming pipelines -> storage -> three suction sections -> separate transmission/distribution pump groups -> separate external outlets. Gravity supplies pump suction; the main pumps provide the onward pressure.
- Reference flow arithmetic is consistent: 200 MIGD = 37,884.083 m3/h; six 25 MIGD duty pumps give 150 MIGD transmission and two give 50 MIGD distribution. One standby and one future bay are shown per current group.
- Individual tank filling/outlet MOVs, normal-open sectioning valves and the normally closed station bypass are present.
- All ten current main-pump discharge positions show an NRV and a downstream isolation valve. Their orientation is consistent with the legend; the filled check-valve half must not be mistaken for a separate wrong-way flow arrow.
- Metering, injection, sampling/analyser and outlet FCV/MOV functions are included. Injection follows metering and precedes sampling.
- Suction bladder surge vessels are correctly separated from the air-compressor supply; discharge vessels have an air-main interface.
- Duty/standby oil-free air compressors with aftercooler/separator and dryer/filter trains, two receivers and a mobile charging connection are included.
- Pump/motor, VFD and air-compressor cooling are deliberately separate. The closed C1 loop returns to HX-701, C2 has supply/return, and C3 is air cooled with no water connection. Electrolyzer CH-501 is a separate package duty.
- Clean/general, hyperchlorination and chemical containment destinations are differentiated conceptually; treatment and compatible chemical segregation still require closure.
- The P-321 future suction crosses the existing distribution discharge without connection, using the drawing gap convention. The principal reciprocal off-sheet service/destination references can be traced across002-005.

## Engineer comments

- R25: carbon filter / softener comment remains open; WS-500 says softener only.
- R26: TK-504 chilled-water/cooling comment remains open; no storage cooling interface is shown and Note3 limits CH-501 to other duties.

## Findings

### R01 - Medium - Design basis / storage (Sheet 001 / 002)

**Location:** T-101 to T-108; 24 h storage statement
**Observed:** Eight tanks labelled 25 MIG give 200 MIG, exactly 24 h at 200 MIGD. The drawing does not identify whether 25 MIG is usable or gross volume.
**Action:** Define gross and usable storage, dead volume, minimum operating level and any reserved volume. If 25 MIG is gross, usable autonomy is less than 24 h. With one nominal 25 MIG tank unavailable, gross autonomy is 21 h; the drawing does not claim 24 h N-1, so confirm whether that is required.
**Close using:** Storage calculation / design basis / PFD note
**Basis:** Calculation required

### R02 - High - Station inlet (Sheet 002)

**Location:** Three typical incoming lines upstream of the common inlet manifold
**Observed:** Each incoming line shows a MOV, FCV and FE/FIT, but no line check valve or stated reverse-flow strategy.
**Action:** Confirm actual incoming line count and network pressure combinations. Establish how backfeeding between live incoming pipelines is prevented or intentionally permitted; show check/isolation arrangements only as required by the network authority and hydraulic study. Do not assume every inlet needs an NRV.
**Close using:** Network interface / hydraulic study / P&ID
**Basis:** Confirmation required

### R03 - Medium - Station inlet (Sheet 002)

**Location:** MOV-101 / FCV-101 / FE-101 typical inlet control
**Observed:** Upstream motorized isolation is shown. Local downstream isolation, FCV maintenance bypass and metering maintenance provisions are not shown.
**Action:** Confirm the maintenance philosophy. Where one inlet control train must remain maintainable with the other lines live, provide suitable isolation on both sides of the equipment. A bypass is conditional, not automatically required. Check meter straight lengths, FCV cavitation/noise and valve fail/closure behavior in the P&ID and calculations.
**Close using:** P&ID / FCV and flowmeter data
**Basis:** P&ID confirmation

### R04 - High - Storage / pump protection (Sheet 002 / 003)

**Location:** LIT-101 (TYP.), tank inlet MOVs and main pumps
**Observed:** A typical level transmitter and tank inlet/outlet MOVs are shown, but the functional high-high filling shutdown and low-low pump protection are not stated.
**Action:** Add the operating philosophy: tank high-high level inhibits/closes the appropriate filling path; tank/header low level or low suction pressure prevents unsafe pump operation. Define valve proof, pump sequencing and independent protection requirements in the P&ID/cause-and-effect. Do not invent trip settings.
**Close using:** PFD note / P&ID / cause-and-effect
**Basis:** Review finding

### R05 - High - Tank drainage (Sheet 002 / 005)

**Location:** Each tank overflow and bottom drain to OP-101
**Observed:** Side overflow and bottom drain connections join dashed lines to OP-101. Individual bottom-drain isolation is not shown.
**Action:** Distinguish the normally closed, isolable bottom drain from the overflow, which must remain available. Document screened/sanitary termination, air gap or equivalent backflow protection, venting and capacity. Prevent lagoon or pit water from reaching potable storage. Do not place an ordinary shutoff valve in the required overflow path.
**Close using:** PFD clarification / tank and drainage P&IDs
**Basis:** Review finding

### R06 - High - Station bypass (Sheet 002 / 003)

**Location:** MOV-102 (NC), inlet manifold to suction header
**Observed:** The inlet-to-suction bypass and its normally closed MOV are present. The pressure transition and mode interlocks are not described.
**Action:** Define bypass mode using actual incoming pressure. Check pressure exposure of the suction system and tank outlet lines, potential reverse filling through tank outlets, NPSH, surge and isolation proof. Determine required pressure reduction, backflow protection and tank-isolation interlocks from the approved arrangement.
**Close using:** Hydraulic study / PFD operating note / P&ID
**Basis:** Confirmation required

### R07 - High - Gravity feed (Sheet 002 / 003)

**Location:** Tank outlet manifold to three suction-header sections
**Observed:** The normal path is correctly shown as storage to suction header to main pumps. No water levels or hydraulic-loss data establish the gravity-feed performance.
**Action:** Verify the hydraulic grade and NPSH available at minimum tank level for both groups, with the intended maximum simultaneous flow and unavailable tanks/sections. Include entrance, manifold, suction-valve and pipe losses; compare against actual pump NPSH requirements and project margin.
**Close using:** Hydraulic / NPSH calculation
**Basis:** Calculation required

### R08 - High - Main pumps (Sheet 003)

**Location:** P-301 to P-307 and P-311 to P-313 suction branches
**Observed:** Discharge NRVs and isolation valves are drawn for all ten current main-pump positions. Individual suction isolation valves are not drawn.
**Action:** Show one suitable suction isolation provision for each current main pump, with future-pump provisions separately identified. Retain the existing discharge sequence pump -> NRV -> isolation -> header. Add pump casing drain/vent and local pressure measurement on the P&ID; confirm valve type and hydraulic impact.
**Close using:** PFD / main-pump P&ID
**Basis:** Review finding

### R09 - High - Header resilience (Sheet 003)

**Location:** Group A and Group B sectioning valves; Note 2
**Observed:** Each discharge header is sectioned, but each has one outlet on the right side. A left-hand section cannot supply that outlet when the intervening sectioning valve is closed.
**Action:** Demonstrate the claim that at least half of each group remains available with any one section isolated. Provide a suitable independently isolable outlet/header arrangement, or narrow the note to the actual supported isolation cases. Check suction and discharge sections together; pump count alone does not prove an available outlet path.
**Close using:** PFD topology / isolation-case hydraulic matrix
**Basis:** Review finding

### R10 - Medium - Future equipment (Sheet 003)

**Location:** P-308, P-314 and future second distribution group P-321
**Observed:** Future pump bays and a future group with separate discharge/surge provision are shown. P-321 is fed from the suction header and crosses S-22 without connection, consistent with the drawing gap convention.
**Action:** Identify installed versus future valves/spools, capped or blinded live tie-ins, and the future duty/standby arrangement. Preserve the separation of the future suction connection from the existing distribution discharge header.
**Close using:** PFD / tie-in schedule / P&ID
**Basis:** Clarification required

### R11 - Medium - Group outlets (Sheet 003)

**Location:** FCV-401 / FCV-411 and their bypasses
**Observed:** Both outlet FCVs have a manual-valve bypass and a downstream common MOV. Separate block valves on the two ends of the FCV leg are not drawn; bypass normal status is unstated.
**Action:** If live FCV maintenance is intended, add isolation at each end of the FCV leg, leaving the bypass path available. The downstream common MOV alone cannot isolate the FCV while bypass flow continues. State NC/secured bypass status and approved manual operation; otherwise document whole-outlet shutdown maintenance.
**Close using:** PFD normal status / outlet P&ID
**Basis:** Review finding

### R12 - High - Pump / outlet control (Sheet 003)

**Location:** VFD pumps, outlet FCVs/MOVs and main headers
**Observed:** VFDs and flow instrumentation are present, but main suction/discharge pressure measurement and the coordinated pressure/flow operating philosophy are not shown.
**Action:** Define how VFD control and outlet FCV control interact, minimum safe pump flow and valve/pump start-stop sequencing. Confirm pressure measurement, low suction/no-flow protection and MOV closure times in the P&ID/cause-and-effect/transient study. The stated 250 m and 100-160 m heads are differential heads, not complete valve or vessel design pressures.
**Close using:** PFD functional note / P&ID / surge study
**Basis:** Review finding

### R13 - Medium - Water quality (Sheet 003)

**Location:** IP-401 / SP-401 / WQM-401 and IP-411 / SP-411 / WQM-411
**Observed:** Metering upstream of injection and sampling/analyser points downstream of injection are correctly sequenced. Sufficient chemical mixing and representative sample conditions are not established.
**Action:** Confirm mixing length or mixer requirements and sample-system design for the actual analytes, especially residual chlorine. Add analyser sample isolation, conditioning and safe drain details in the P&ID. Do not infer adequate contact or mixing from schematic spacing.
**Close using:** Mixing calculation / analyser data / P&ID
**Basis:** Confirmation required

### R14 - Medium - Suction surge vessels (Sheet 003)

**Location:** SV-201 / SV-202 / SV-203 typical pairs
**Observed:** Each suction section has bladder vessels behind one common water-side isolation valve. The note correctly excludes them from the compressed-air system.
**Action:** Confirm individual-vessel or train maintenance isolation, safe drain/vent and manufacturer-approved precharge provisions. Prove sufficient surge protection for permitted out-of-service cases. Keep the required bidirectional hydraulic response; do not add an ordinary NRV to the vessel water connection without a deliberately engineered surge arrangement.
**Close using:** Surge study / vessel vendor P&ID
**Basis:** Review finding

### R15 - High - Discharge surge trains (Sheet 003)

**Location:** SV-401 and SV-411, Train 1 and Train 2
**Observed:** For each group, one takeoff valve feeds Train 1, followed by a second water-line valve between Train 1 and Train 2. This isolates Train 2 alone, or both trains; it cannot isolate Train 1 while retaining Train 2.
**Action:** Provide independently isolable parallel train branches, or another arrangement that demonstrably meets the required maintenance cases. Show protected normal-open status, independent air-side isolation/control, drains/vents and the remaining active surge capacity. Revalidate the arrangement by transient analysis.
**Close using:** PFD topology / surge study / vendor P&ID
**Basis:** Review finding

### R16 - High - Surge compressed air (Sheet 003 / 005)

**Location:** Common S-14 air main to transmission and distribution surge vessels
**Observed:** The same common air main supplies both groups, despite their different pump head bands. Per-group or per-vessel air pressure/level controls and water-backflow safeguards are not shown.
**Action:** Establish actual vessel operating/charge pressures and provide the required regulated/control branches, isolation, NRVs or equivalent water-backflow safeguards and pressure/level protection. A 250 m water head is about 24.52 bar differential; 100-160 m is about 9.81-15.69 bar. Add suction/static pressure and transient limits before selecting compressor or receiver ratings; these conversions are not setpoints.
**Close using:** Surge / compressor sizing / vendor P&ID
**Basis:** Confirmation required

### R17 - High - Compressor packages (Sheet 005)

**Location:** C-601 / C-602, DR-601 / DR-602 to common receiver feed
**Observed:** Oil-free duty/standby compressors, intake equipment, aftercooler/separator and dryer/filter trains are present. Separate discharge NRVs and maintenance isolation are not drawn before the trains join.
**Action:** Confirm these devices within the package and show/reference the outlet isolation and non-return function so a live receiver cannot backfeed the standby/open compressor train. Verify separator/aftercooler/dryer drains and discharge destinations. Confirm air quality and dew point against the actual W-M-SS-007 requirements.
**Close using:** Compressor package P&ID / project specification
**Basis:** P&ID/OEM confirmation

### R18 - High - Air receivers (Sheet 005)

**Location:** V-601 / V-602
**Observed:** Two receivers are connected to common upstream/downstream air lines. Individual isolation, pressure indication, safety relief and low-point condensate drains are not drawn.
**Action:** Confirm individual service isolation and receiver safety relief/pressure indication/drainage in the vendor P&ID. Relief protection must remain effective for every permitted isolation state; ordinary maintenance valves must not defeat required vessel protection. Establish working/design pressure from the surge duty.
**Close using:** Receiver data / vendor P&ID
**Basis:** P&ID/OEM confirmation

### R19 - Medium - Mobile compressor connection (Sheet 005)

**Location:** MC-601
**Observed:** A manual valve and capped-looking connection are drawn at the common air main. Backflow prevention and the mobile source pressure/quality limits are not stated.
**Action:** Confirm a positively capped/blinded connection, isolation and suitable NRV/backflow safeguard, with approved pressure regulation and connection procedure. The mobile source must meet the required pressure and air quality; prevent uncontrolled charging or discharge toward disconnected equipment.
**Close using:** P&ID / charging procedure
**Basis:** P&ID confirmation

### R20 - Medium - Service water (Sheet 005)

**Location:** P-801 / P-802 and utility branches
**Observed:** Duty/standby pumps each have a discharge NRV. Individual suction/discharge isolation and consumer branch isolation are not drawn.
**Action:** Confirm service-pump maintenance isolation, pressure control/protection and isolation for washdown, domestic water, disinfection and cooling makeup. Retain the two existing pump NRVs. Confirm independent domestic/potable and process-service classifications with the water authority.
**Close using:** Service-water P&ID
**Basis:** P&ID confirmation

### R21 - High - Potable backflow protection (Sheet 004 / 005)

**Location:** S-41 to WS-500 and service-water supply to P-703
**Observed:** Potable-derived service water supplies the salt/chemical process and an inhibitor-containing cooling loop; hazard-appropriate backflow protection is not shown.
**Action:** Provide an approved separation/backflow arrangement at the chemical pretreatment/process supply and cooling-makeup interface, and at other hazardous utility consumers. Select air gap or appropriate tested devices according to the actual hazard and authority requirements; a pump NRV alone is not complete contamination protection.
**Close using:** PFD interface note / water authority / P&ID
**Basis:** Review finding

### R22 - High - Pump / motor cooling (Sheet 005)

**Location:** HX-701 / P-702 / HX-707 closed loop
**Observed:** A closed cooling circuit, heat-rejection interface, main pump/motor coolers and a parallel lube-oil HX are shown. Equipment quantities, heat rejection type, duties and loss-of-cooling behavior are unstated.
**Action:** Define the actual primary/secondary heat-rejection arrangement and ambient design conditions, pump/motor/lube-oil heat loads, supply/return temperatures, flow and redundancy. Confirm cooling proof and temperature/low-flow protection required for the main pumps. The two HX circuits must remain hydraulically distinct where indirect exchange is intended.
**Close using:** PFD equipment duties / OEM thermal design / P&ID
**Basis:** Calculation/OEM confirmation

### R23 - Medium - Cooling piping (Sheet 005)

**Location:** P-702 / P-703; F-704 / V-705 / X-706; cooler branches
**Observed:** Filters, expansion/pressure vessel and inhibitor dosing are combined in one box connected by a single branch. Component piping roles and maintenance/balancing valves are not shown.
**Action:** Clarify whether filtration is full-flow or side-stream; show the expansion connection and dosing injection separately. Confirm circulation/makeup pump NRVs where needed, isolations, cooler branch isolation/balancing, vents, drains and pressure/thermal relief. Define the allowable condition when an expansion-vessel connection is isolated.
**Close using:** Cooling P&ID / package diagram
**Basis:** P&ID confirmation

### R24 - High - VFD cooling (Sheet 005)

**Location:** C2 drive-OEM package and VFD units
**Observed:** Supply and return are shown between a generic VFD cooling package and the drives. The ultimate heat sink, heat load and failure response are not identified.
**Action:** State whether the OEM system rejects heat to ambient air, a dedicated chiller or another separately defined circuit. Add its required external interfaces and thermal duty; confirm flow/temperature monitoring, maintenance isolation and drive derating/trip behavior. Do not connect it to C1 or CH-501 merely to close the drawing.
**Close using:** PFD interface / VFD OEM cooling design
**Basis:** OEM confirmation

### R25 - Medium - Electrolyzer pretreatment (Sheet 004)

**Location:** WS-500
**Observed:** WS-500 is labelled SOFTENER SKID only. The engineer requested carbon filter / softener skid.
**Action:** Revise the label to CARBON FILTER / SOFTENER SKID and identify the actual process arrangement and package boundary. Confirm treated-water chlorine/hardness quality and consumables/regeneration against the electrolyzer vendor; the revised label must match the actual supplied equipment.
**Close using:** PFD / vendor pretreatment package
**Basis:** Engineer comment 1 - not closed

### R26 - Medium - NaOCl storage cooling (Sheet 004)

**Location:** TK-504 and CH-501; Sheet 004 Note 3
**Observed:** No chilled-water supply/return or storage cooling interface is shown at TK-504. CH-501 and Note 3 explicitly identify softener/electrolyzer duties only.
**Action:** Add a clearly marked chilled-water supply/return or dedicated storage-cooling interface/note for TK-504 as requested. Update CH-501 duty description and Note 3 if it also serves storage. Select an OEM-approved indirect cooling method (jacket/coil/external HX as applicable), rather than connecting chilled water into the chemical contents. Confirm storage temperature, compatible materials and cooling duty.
**Close using:** PFD / thermal duty / vendor storage design
**Basis:** Engineer comment 2 - not closed

### R27 - Medium - Electrolyzer feed / chilled water (Sheet 004)

**Location:** CH-501 drawn in the softened-water feed route
**Observed:** The route from WS-500 passes through the CH-501 symbol to EL-503 as one process line. No separate chilled-water circuit is drawn.
**Action:** Clarify whether this is cooled softened process water through an integrated feed-water chiller or an indirect chilled-water HX. Identify the cooled process stream and external CHWS/CHWR interfaces separately, with the required circulation/temperature control. A chilled-water plant label alone does not define the fluid circuits.
**Close using:** PFD process definition / vendor P&ID
**Basis:** Clarification required

### R28 - High - Hypochlorite dosing (Sheet 003 / 004)

**Location:** P-506 split to S-16 / IP-401 and S-17 / IP-411
**Observed:** One typical dosing pump discharges to two branches without drawn independent metering or injection NRV/isolation. The receiving headers operate at different head bands.
**Action:** Show independent controllable dosing duties for each header: separate dosing trains or a proven common skid with independent branch metering/control. Confirm injection check/isolation, pressure capability, required backpressure devices and dosing-pump relief to a compatible contained destination. Prevent process water reaching TK-504 or transferring between headers through chemical piping. Base dosage on each measured water flow and approved residual-control philosophy.
**Close using:** PFD dosing arrangement / dosing calculations / P&ID
**Basis:** Review finding

### R29 - High - Hydrogen ventilation (Sheet 004)

**Location:** EL-503 / TK-504 / B-505 hydrogen vent
**Observed:** A tank hydrogen vent and dilution-air blower are correctly shown. Ventilation proof, hydrogen handling at the electrolyzers and loss-of-dilution response are not defined.
**Action:** Confirm the OEM hydrogen generation, dilution and vent route for both cells and storage; verify safe termination and gas accumulation avoidance. Define blower duty/standby requirements, ventilation proof/interlock and hydrogen detection where required by the actual hazard assessment. No hydrogen limits, air rates or area classification can be selected from this PFD alone.
**Close using:** PFD functional note / OEM design / hazard assessment
**Basis:** Review finding

### R30 - High - Chemical containment (Sheet 004 / 005)

**Location:** TK-505 HCl / TK-504 NaOCl / UB-501 / CS-821
**Observed:** Bund drainage is represented as one stream to one chemical containment item. Separate acid and hypochlorite spill paths are not demonstrated.
**Action:** Show physically segregated HCl and hypochlorite containment/drain paths or a specifically engineered compatible arrangement. Mixing acid and hypochlorite can release chlorine gas. State normally closed controlled bund-drain operation and identify sampling/collection/disposal; do not route both uncontrolled spill streams to one common sump.
**Close using:** PFD segregation / chemical drainage P&ID / containment design
**Basis:** Review finding

### R31 - Medium - Package effluents (Sheet 004 / 005)

**Location:** WS-500 / TK-501 / TK-505 / EL-503
**Observed:** Carbon/softener backwash or regeneration waste, brine/process reject and acid-cleaning effluent destinations are not identified.
**Action:** Identify the actual waste streams, quantities and compatible containment/treatment destinations. Show the cleaning transfer/flush function and containment of acid-cleaning effluent. Distinguish brine, acid, hypochlorite and ordinary washdown; the exact package valving belongs in its P&ID.
**Close using:** PFD waste interfaces / vendor P&ID / treatment design
**Basis:** Confirmation required

### R32 - High - Pump-hall sump (Sheet 005)

**Location:** P-811 / P-812 discharge to TK-831
**Observed:** Two submersible pumps join a common discharge without drawn individual NRVs or discharge isolation.
**Action:** Confirm an individual discharge NRV and service isolation for each sump pump so the duty pump cannot send water through the standby pump into the pit. Add level-based duty/standby controls, high-high alarm and usable sump/holding volumes in the P&ID and drainage calculations.
**Close using:** Drainage P&ID / sump sizing
**Basis:** Review finding

### R33 - High - Header drainage (Sheet 003 / 005)

**Location:** Typical header drain valve to TK-831
**Observed:** One typical drain takeoff is shown on the Group B discharge, with a connection to the drainage holding tank. Complete isolated-section drains and controlled depressurization are not demonstrated.
**Action:** Provide the necessary low-point drains and high-point venting for suction/discharge and isolated sections, based on the actual pipe profile. Establish safe staged pressure letdown, receiving-tank venting and energy dissipation for high-pressure discharge-header drainage. Avoid an uncontrolled pressurized connection into a civil holding tank.
**Close using:** PFD drain note / P&ID / depressurization calculation
**Basis:** Review finding

### R34 - High - NaOCl product drainage (Sheet 004 / 005)

**Location:** TK-504 bottom drain to LG-102 labelled HYPERCHLORINATION DRAINAGE
**Observed:** The chemical storage tank bottom drain goes directly to the hyperchlorination-water lagoon route. Product-drain concentration and lagoon suitability are not stated.
**Action:** Distinguish stock hypochlorite product drains from chlorinated pipeline/disinfection wash water. Route concentrated product to a compatible contained collection/treatment system, or explicitly prove LG-102 is designed for that duty. Identify concentration, volume, controlled drain procedure and treatment before any release.
**Close using:** PFD destination / chemical-drainage and treatment design
**Basis:** Review finding

### R35 - High - Lagoon transfer / discharge (Sheet 005)

**Location:** LG-102 and LG-103 transfer to LG-101; storm-water connection
**Observed:** Both drain lagoons connect to a transfer route to LG-101, which has an overflow/bypass to storm water. No controlled release, dechlorination or water-quality acceptance function is shown.
**Action:** Define gravity/pumped transfer and reverse-flow prevention from actual levels. Hold and dechlorinate hyperchlorination effluent to the approved discharge criterion before transfer/release. Confirm contaminated pump-hall water acceptance/treatment, transfer isolation and monitoring, lagoon/overflow capacity and authority approval for the storm-water interface.
**Close using:** PFD treatment/release function / drainage P&ID / discharge approval
**Basis:** Review finding

### R36 - Medium - Pump-hall drainage quality (Sheet 005)

**Location:** Pump/motor/lube-oil areas to PT-811 / LG-103
**Observed:** Lube-oil heat-exchange equipment is shown and floor/pump/valve drainage joins LG-103. Treatment or separate containment of possible oil-contaminated water is unstated.
**Action:** Confirm whether the actual pump/lube equipment can introduce oil into floor drains. If so, provide suitable containment/separation and controlled disposal before clean drainage/storm-water release; otherwise record the clean-drain basis. Do not assume every pump-hall drain automatically requires an oil separator.
**Close using:** Drainage classification / OEM leakage data / treatment design
**Basis:** Confirmation required

### R37 - Medium - Review scope / traceability (Sheet 001-005)

**Location:** Referenced W-G-SS-017, W-M-SS-007 and N14054 typical P&IDs
**Observed:** The cited specifications, reference P&IDs, vendor package P&IDs and detailed hydraulic/transient studies were not supplied with this five-sheet PDF.
**Action:** Use the reviewed PFD as a functional baseline, then reconcile it with the actual project and package P&IDs, valve schedules and approved studies. This review cannot establish that every installed valve exists or verify the cited standard clauses, sizes, pressure classes or settings.
**Close using:** Referenced specifications / P&IDs / vendor data
**Basis:** Review limitation

### R38 - Low - Standard drawing clarity (Sheet 001 / 002 / 003)

**Location:** Band-3 scalability table and functional/TYP tags
**Observed:** The Band-3 example table includes 100 MIGD, while the stated band definition places 100 MIGD in Band 2. Several repeated valves/vessels use a single functional or typical tag.
**Action:** Label 100 MIGD as a boundary example or align the table with the band definition. Retain functional/TYP identification at PFD level if intended, but assign unique equipment and valve identities when the project P&IDs/schedules are issued. Do not count each typical symbol as a certified bill of materials.
**Close using:** PFD editorial clarification / project tag schedule
**Basis:** Drawing clarity

## Valve checklist

| Sheet | Location | Provision | Status | Review |
|---|---|---|---|---|
| 002 | Incoming supply control | 3 typical lines: MOV + FCV each | Present | Check inlet isolation/backflow strategy and live maintenance; R02-R03 |
| 002 | Tank inlet/outlet | 8 inlet MOVs + 8 outlet MOVs | Present | Level control and proof; R04. Functional tags require project identities. |
| 002 | Tank outlet sectioning | 2 manual section valves marked NO | Present | Check gravity flow and isolation cases; R07/R09 |
| 002 / 003 | Station bypass | MOV-102 marked NC | Present | Pressure suitability and bypass-mode interlocks; R06 |
| 002 | Service-water takeoff | 1 manual branch isolation | Present | Additional service-pump/consumer isolations on Sheet005; R20 |
| 002 | Fire-water storage takeoff | 1 manual isolation | Present | Confirm sanitary separation/backflow at actual fire-water storage interface in its P&ID. |
| 002 | Tank bottom drains | Individual drain valves for 8 tanks | Not shown | Normally closed drain isolation; retain available overflow; R05 |
| 003 | Main-pump discharges | 10 current pump positions: NRV + isolation each | Present | Correct relative sequence and orientation against legend; future symbols excluded from current count. |
| 003 | Main-pump suctions | 10 current pump positions: individual suction isolation | Not shown | Add suitable individual pump suction isolation; R08 |
| 003 | Suction header | 2 section valves marked NO | Present | Three sections with both pump groups served; hydraulic/availability proof pending. |
| 003 | Discharge headers | 1 section valve for A and 1 for B, marked NO | Present | Single-end outlets do not prove all isolation cases; R09 |
| 003 | Group outlets | FCV-401 / 411; MOV-401 / 411; 2 bypass valves | Present | Bypass NC status and FCV-leg maintenance blocks require clarification; R11 |
| 003 | FCV maintenance legs | Separate upstream/downstream FCV-leg blocks | Not shown | Needed if live FCV removal through bypass is intended; R11 |
| 003 | Water-quality sample taps | SP-101 on002; SP-401 / 411 on003 with tap valves | Present | Confirm analyser sample-system isolation/conditioning and representative mixing; R13 |
| 003 | Suction surge | 1 common isolation for each of 3 typical vessel pairs | Present / incomplete maintenance detail | Individual-vessel isolation/drain/precharge and N-1 surge adequacy; R14 |
| 003 | Discharge surge | Each group: common takeoff valve + valve between trains | Present / topology issue | Not independently isolable in both directions; R15 |
| 003 / 004 | Chemical injection | Branch injection NRV and isolation at each header | Not shown | Independent dosing and cross-pressure backflow protection; R28 |
| 003 | Header drains | 1 drain symbol marked TYP on B discharge | Present / coverage unproven | Other isolated sections and controlled pressure letdown require confirmation; R33 |
| 004 | NaOCl storage drain | 1 tank-bottom drain valve | Present / destination issue | Product drain to hyperchlorination route requires compatible collection/treatment; R34 |
| 004 / 005 | Chemical bund drains | Controlled, segregated acid/NaOCl drain valves | Not shown | Segregated containment and NC controlled bund release; R30 |
| 005 | Service-pump discharges | 1 NRV on each of P-801 / P-802 | Present | Suction/discharge service isolation not shown; R20 |
| 005 | Cooling / chemical water makeup | Hazard-appropriate potable backflow protection | Not shown | Select approved separation at each hazardous interface; R21 |
| 005 | Compressor discharge trains | Independent NRV and outlet maintenance isolation | Not shown at PFD level | Confirm vendor package devices before common receiver feed; R17 |
| 005 | Air receivers | Service isolation, safety relief and condensate drains | Not shown at PFD level | Confirm protection in every permitted isolation state; R18 |
| 005 | Mobile air source | Manual isolation at MC-601 | Present / detail incomplete | Cap/blind, NRV and pressure/quality safeguards; R19 |
| 005 | Cooling loop components | Local isolation/check/balancing/vent/drain/relief functions | Not shown at PFD level | Confirm actual cooling package/P&ID; R23 |
| 005 | Sump-pump discharges | Individual NRV and isolation for P-811 / P-812 | Not shown | Avoid flow back through standby pump; R32 |
| 005 | Lagoon transfers | Controlled transfer/release and reverse-flow protection | Not shown | Treatment and approved release philosophy; R35 |

Source SHA256: 638866ff604c3500a8b0c72dd666cb8e8cc7863817889240f42996c32450021b
