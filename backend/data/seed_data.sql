-- Enable the uuid-ossp extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create departments table
CREATE TABLE departments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL,
  head_id UUID REFERENCES employees(id) -- This will require employees table to exist, so consider altering after creation.
);

-- Create employees table
CREATE TABLE employees (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  department_id UUID REFERENCES departments(id),
  designation VARCHAR(100),
  date_joined DATE NOT NULL
);

-- Create assets table
CREATE TABLE assets (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL,
  department_id UUID REFERENCES departments(id),
  purchased_on DATE NOT NULL,
  warranty_period INT, -- Warranty period in months
  status VARCHAR(50) -- Status: active, maintenance, retired
);

-- Create maintenance_logs table
CREATE TABLE maintenance_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  maintenance_date DATE NOT NULL,
  cost DECIMAL(10, 2)
);

-- Create vendors table
CREATE TABLE vendors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL,
  contact_email VARCHAR(100),
  contact_phone VARCHAR(15)
);

-- Create asset_vendor_link table for many-to-many relationship between assets and vendors
CREATE TABLE asset_vendor_link (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
  vendor_id UUID REFERENCES vendors(id) ON DELETE CASCADE
);

-- Sample inserts for departments
INSERT INTO departments (id, name) VALUES (uuid_generate_v4(), 'IT');
INSERT INTO departments (id, name) VALUES (uuid_generate_v4(), 'HR');

-- Sample inserts for employees
INSERT INTO employees (id, name, email, department_id, designation, date_joined)
VALUES (uuid_generate_v4(), 'John Doe', 'john@example.com', (SELECT id FROM departments WHERE name='IT'), 'Technician', '2023-01-10');

INSERT INTO employees (id, name, email, department_id, designation, date_joined)
VALUES (uuid_generate_v4(), 'Jane Smith', 'jane@example.com', (SELECT id FROM departments WHERE name='HR'), 'HR Manager', '2022-05-15');

-- Sample inserts for assets
INSERT INTO assets (id, name, department_id, purchased_on, warranty_period, status)
VALUES (uuid_generate_v4(), 'Laptop A', (SELECT id FROM departments WHERE name='IT'), '2022-01-15', 36, 'active');

INSERT INTO assets (id, name, department_id, purchased_on, warranty_period, status)
VALUES (uuid_generate_v4(), 'Printer B', (SELECT id FROM departments WHERE name='HR'), '2021-12-20', 24, 'maintenance');

-- Sample inserts for vendors
INSERT INTO vendors (id, name, contact_email, contact_phone)
VALUES (uuid_generate_v4(), 'Vendor X', 'vendorx@example.com', '1234567890');

INSERT INTO vendors (id, name, contact_email, contact_phone)
VALUES (uuid_generate_v4(), 'Vendor Y', 'vendory@example.com', '9876543210');

-- Sample inserts for asset_vendor_link
INSERT INTO asset_vendor_link (id, asset_id, vendor_id)
VALUES (uuid_generate_v4(), (SELECT id FROM assets WHERE name='Laptop A'), (SELECT id FROM vendors WHERE name='Vendor X'));

INSERT INTO asset_vendor_link (id, asset_id, vendor_id)
VALUES (uuid_generate_v4(), (SELECT id FROM assets WHERE name='Printer B'), (SELECT id FROM vendors WHERE name='Vendor Y'));

-- Sample inserts for maintenance_logs
INSERT INTO maintenance_logs (id, asset_id, description, maintenance_date, cost)
VALUES (uuid_generate_v4(), (SELECT id FROM assets WHERE name='Printer B'), 'Replaced toner cartridge', '2023-03-10', 50.00);

INSERT INTO maintenance_logs (id, asset_id, description, maintenance_date, cost)
VALUES (uuid_generate_v4(), (SELECT id FROM assets WHERE name='Laptop A'), 'Battery replacement', '2023-02-25', 150.00);

-- Alter departments table to set foreign key for head_id
ALTER TABLE departments ADD CONSTRAINT fk_head_id FOREIGN KEY (head_id) REFERENCES employees(id);
