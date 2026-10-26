-- MARTS: curated tables the semantic layer reads. The Executive summary reads only these.

CREATE VIEW mart_opportunity AS SELECT * FROM fact_opportunity;

CREATE VIEW mart_opportunity_snapshot AS
SELECT s.*, f.vertical, f.lead_practice, f.primary_platform, f.account_id, f.client_partner_upn,
       f.lead_source, f.geography, f.offering_class, f.partner, f.campaign_id,
       f.workshop_originated, f.created_date
FROM fact_opportunity_snapshot s
JOIN fact_opportunity f USING (opportunity_id);

CREATE VIEW mart_target AS SELECT * FROM fact_target;
