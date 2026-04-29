#!/usr/bin/env python3
"""
Example script: Loading and exploring the Aegis AI Hugging Face dataset.

This script demonstrates how to:
1. Load the insurance underwriting risk dataset from Hugging Face
2. Explore its structure and statistics
3. Apply Aegis AI feature engineering
4. Prepare data for model training
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from ml_engine.features import engineer_features, get_feature_matrix, FEATURE_COLUMNS


def load_hf_dataset():
    """Load the dataset from Hugging Face Hub."""
    print("📊 Loading Hugging Face dataset...")
    print("   Dataset: OMG091213/gcc-insurance-underwriting-risk\n")
    
    try:
        from datasets import load_dataset
        ds = load_dataset("OMG091213/gcc-insurance-underwriting-risk")
        df = ds['train'].to_pandas()
        print(f"✓ Loaded {len(df):,} rows")
        return df
    except ImportError:
        print("❌ ERROR: 'datasets' package not installed.")
        print("   Install with: pip install datasets>=2.15.0")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR loading dataset: {e}")
        sys.exit(1)


def explore_dataset(df):
    """Display basic dataset statistics."""
    print("\n" + "="*60)
    print("DATASET OVERVIEW")
    print("="*60)
    
    print(f"\n📈 Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    
    print(f"\n📋 Columns ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        dtype = str(df[col].dtype)
        null_pct = (df[col].isna().sum() / len(df) * 100)
        print(f"   {i:2d}. {col:25s} ({dtype:12s}) - {null_pct:5.1f}% missing")
    
    print("\n📊 Feature Statistics:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    print(df[numeric_cols].describe().to_string())
    
    # Check for target variable
    if 'loss_ratio' in df.columns:
        print(f"\n🎯 Target Variable (loss_ratio):")
        print(f"   Min:  {df['loss_ratio'].min():.4f}")
        print(f"   Q1:   {df['loss_ratio'].quantile(0.25):.4f}")
        print(f"   Mean: {df['loss_ratio'].mean():.4f}")
        print(f"   Q3:   {df['loss_ratio'].quantile(0.75):.4f}")
        print(f"   Max:  {df['loss_ratio'].max():.4f}")


def check_feature_compatibility(df):
    """Check which expected features are present in the dataset."""
    print("\n" + "="*60)
    print("FEATURE COMPATIBILITY")
    print("="*60)
    
    available = [col for col in FEATURE_COLUMNS if col in df.columns]
    missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
    
    print(f"\n✓ Available features: {len(available)}/{len(FEATURE_COLUMNS)}")
    for col in available:
        print(f"   ✓ {col}")
    
    if missing:
        print(f"\n⚠ Missing features: {len(missing)}")
        print("   (These will be filled with defaults during feature engineering)")
        for col in missing:
            print(f"   ⊘ {col}")


def apply_feature_engineering(df):
    """Apply Aegis feature engineering pipeline."""
    print("\n" + "="*60)
    print("APPLYING FEATURE ENGINEERING")
    print("="*60)
    
    print("\n🔧 Engineering features...")
    df_engineered = engineer_features(df)
    
    print(f"✓ Features engineered")
    print(f"   Input shape:  {df.shape}")
    print(f"   Output shape: {df_engineered.shape}")
    
    # Get feature matrix
    X, y, feature_names = get_feature_matrix(df_engineered)
    
    print(f"\n📊 Feature Matrix:")
    print(f"   X shape:  {X.shape}")
    print(f"   y shape:  {y.shape if y is not None else 'None'}")
    print(f"   Features: {len(feature_names)}")
    
    print(f"\n🏷 Feature Names:")
    for i, name in enumerate(feature_names, 1):
        print(f"   {i:2d}. {name}")
    
    return X, y, feature_names


def data_quality_report(df):
    """Generate a data quality report."""
    print("\n" + "="*60)
    print("DATA QUALITY REPORT")
    print("="*60)
    
    print("\n✓ Completeness:")
    total_cells = len(df) * len(df.columns)
    missing_cells = df.isna().sum().sum()
    completeness = (1 - missing_cells / total_cells) * 100
    print(f"   {completeness:.1f}% complete ({missing_cells:,} missing values)")
    
    print("\n✓ Duplicates:")
    if 'employee_id' in df.columns:
        duplicates = df['employee_id'].duplicated().sum()
        print(f"   {duplicates} duplicate employee IDs")
    
    print("\n✓ Data Types:")
    print(f"   Numeric:  {len(df.select_dtypes(include=[np.number]).columns)}")
    print(f"   Object:   {len(df.select_dtypes(include=['object']).columns)}")
    print(f"   Other:    {len(df.select_dtypes(exclude=[np.number, 'object']).columns)}")
    
    print("\n✓ Value Ranges:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols[:5]:  # Show first 5 numeric columns
        print(f"   {col:25s}: [{df[col].min():.2f}, {df[col].max():.2f}]")


def main():
    """Main execution."""
    print("\n" + "="*60)
    print("🛡️  AEGIS AI — Hugging Face Dataset Explorer")
    print("="*60)
    
    # Load dataset
    df = load_hf_dataset()
    
    # Explore
    explore_dataset(df)
    check_feature_compatibility(df)
    data_quality_report(df)
    
    # Apply feature engineering
    X, y, feature_names = apply_feature_engineering(df)
    
    # Summary
    print("\n" + "="*60)
    print("✓ SUMMARY")
    print("="*60)
    print(f"\n✓ Dataset loaded and processed successfully")
    print(f"✓ {len(df):,} records ready for training")
    print(f"✓ {X.shape[1]} features prepared")
    print(f"✓ Target variable: {'present' if y is not None else 'absent'}")
    
    print("\n💡 Next steps:")
    print("   1. Run: python -m ml_engine.training.train --use-hf-dataset")
    print("   2. View results in MLflow: mlflow ui")
    print("   3. Deploy the trained model: python ingestion/main.py")
    print("\n")


if __name__ == "__main__":
    main()
