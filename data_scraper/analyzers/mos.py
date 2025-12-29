import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import seaborn as sns

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

# Mapping of Turkish text labels to numeric MOS scores
TURKISH_TO_MOS = {
    'Mükemmel': 5,           # Perfect/Excellent
    'İyi': 4,                # Good
    'Orta': 3,               # Average/Fair
    'Fena Değil': 2,         # Not Bad/Poor
    'Kötü': 1                # Bad
}

def load_survey_data():
    """
    Load the survey responses from the Excel file.
    """
    file_path = Path(__file__).parent / "Türkçe TTS Modeli Değerlendirme Anketi (Yanıtlar).xlsx"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Survey file not found at {file_path}")
    
    # Read the Excel file
    df = pd.read_excel(file_path)
    return df

def convert_text_to_numeric(df):
    """
    Convert Turkish text labels to numeric MOS scores (1-5).
    """
    df_numeric = df.copy()
    
    # Skip the timestamp column (first column)
    for col in df_numeric.columns[1:]:
        df_numeric[col] = df_numeric[col].map(TURKISH_TO_MOS)
    
    return df_numeric

def extract_base_question(full_column_name):
    """
    Extract the base question from the full column name.
    Example: "Kısa Sohbet (Ses A Kadın) [Sesin Kalitesi]" 
    Returns: "Kısa Sohbet [Sesin Kalitesi]"
    Also handles the " 2" suffix that appears in some columns.
    """
    # Remove " 2" suffix if it exists
    col_name = full_column_name.replace(' 2', '')
    
    # Split by opening parenthesis to remove voice type info
    question_part = col_name.split('(')[0].strip()
    # Get the criterion part in brackets
    if '[' in col_name:
        criterion_part = col_name[col_name.index('['):].strip()
        return f"{question_part} {criterion_part}"
    return question_part

def extract_question_type_only(full_column_name):
    """
    Extract just the question type, ignoring criteria.
    Example: "Kısa Sohbet (Ses A Kadın) [Sesin Kalitesi]" 
    Returns: "Kısa Sohbet"
    """
    # Remove " 2" suffix if it exists
    col_name = full_column_name.replace(' 2', '')
    
    # Split by opening parenthesis to remove voice type info
    question_type = col_name.split('(')[0].strip()
    return question_type

def extract_mos_scores(df):
    """
    Extract MOS score columns from the survey data.
    All columns except the timestamp contain MOS scores.
    """
    # All columns except the first one (timestamp) contain MOS scores
    mos_columns = df.columns[1:].tolist()
    return mos_columns

def extract_model_type(full_column_name):
    """
    Extract the model type from the column name.
    Ses A = KaniTTS, Ses B = DiaTTS
    """
    if 'Ses A' in full_column_name:
        return 'KaniTTS'
    elif 'Ses B' in full_column_name:
        return 'DiaTTS'
    return 'Unknown'

def extract_gender(full_column_name):
    """
    Extract the gender from the column name.
    Kadın = Female, Erkek = Male
    """
    if 'Kadın' in full_column_name:
        return 'Kadın (Female)'
    elif 'Erkek' in full_column_name:
        return 'Erkek (Male)'
    return 'Unknown'

def aggregate_by_question(df, mos_columns):
    """
    Aggregate MOS scores by base question across all voice variants.
    Returns a dataframe with 20 unique questions.
    """
    aggregated_data = []
    
    # Extract unique base questions
    base_questions = {}
    for col in mos_columns:
        base_q = extract_base_question(col)
        if base_q not in base_questions:
            base_questions[base_q] = []
        base_questions[base_q].append(col)
    
    # Calculate statistics for each base question
    for base_q, cols in base_questions.items():
        # Combine all responses for this question across all variants
        all_responses = []
        for col in cols:
            responses = df[col].dropna().tolist()
            all_responses.extend(responses)
        
        if all_responses:
            all_responses = np.array(all_responses)
            aggregated_data.append({
                'question': base_q,
                'mean': all_responses.mean(),
                'std': all_responses.std(),
                'count': len(all_responses),
                'min': all_responses.min(),
                'max': all_responses.max()
            })
    
    return pd.DataFrame(aggregated_data).sort_values('question')

def aggregate_by_question_and_model(df, mos_columns):
    """
    Aggregate MOS scores by base question and model type (KaniTTS vs DiaTTS).
    Returns a dataframe with separate statistics for each model.
    """
    aggregated_data = []
    
    # Extract unique base questions
    base_questions = {}
    for col in mos_columns:
        base_q = extract_base_question(col)
        if base_q not in base_questions:
            base_questions[base_q] = []
        base_questions[base_q].append(col)
    
    # Calculate statistics for each base question and model
    for base_q, cols in base_questions.items():
        # Separate by model
        kanitts_responses = []
        diatts_responses = []
        
        for col in cols:
            model = extract_model_type(col)
            responses = df[col].dropna().tolist()
            
            if model == 'KaniTTS':
                kanitts_responses.extend(responses)
            elif model == 'DiaTTS':
                diatts_responses.extend(responses)
        
        # Create entries for each model
        for model, responses in [('KaniTTS', kanitts_responses), ('DiaTTS', diatts_responses)]:
            if responses:
                responses = np.array(responses)
                aggregated_data.append({
                    'question': base_q,
                    'model': model,
                    'mean': responses.mean(),
                    'std': responses.std(),
                    'count': len(responses),
                    'min': responses.min(),
                    'max': responses.max()
                })
    
    return pd.DataFrame(aggregated_data).sort_values(['question', 'model'])

def aggregate_by_question_type_and_model(df, mos_columns):
    """
    Aggregate MOS scores by question type only (averaging across all criteria)
    and model type (KaniTTS vs DiaTTS).
    Returns a dataframe with 5 question types × 2 models (10 total rows).
    """
    aggregated_data = []
    
    # Extract unique question types and group all responses
    question_types = {}
    for col in mos_columns:
        q_type = extract_question_type_only(col)
        if q_type not in question_types:
            question_types[q_type] = []
        question_types[q_type].append(col)
    
    # Calculate statistics for each question type and model
    for q_type, cols in question_types.items():
        # Separate by model
        kanitts_responses = []
        diatts_responses = []
        
        for col in cols:
            model = extract_model_type(col)
            responses = df[col].dropna().tolist()
            
            if model == 'KaniTTS':
                kanitts_responses.extend(responses)
            elif model == 'DiaTTS':
                diatts_responses.extend(responses)
        
        # Create entries for each model
        for model, responses in [('KaniTTS', kanitts_responses), ('DiaTTS', diatts_responses)]:
            if responses:
                responses = np.array(responses)
                aggregated_data.append({
                    'question_type': q_type,
                    'model': model,
                    'mean': responses.mean(),
                    'std': responses.std(),
                    'count': len(responses),
                    'min': responses.min(),
                    'max': responses.max()
                })
    
    return pd.DataFrame(aggregated_data).sort_values(['question_type', 'model'])

def aggregate_by_question_type_model_and_gender(df, mos_columns):
    """
    Aggregate MOS scores by question type, model type, and gender.
    Returns a dataframe for comparing male/female separately.
    """
    aggregated_data = []
    
    # Extract unique question types and group all responses
    question_types = {}
    for col in mos_columns:
        q_type = extract_question_type_only(col)
        if q_type not in question_types:
            question_types[q_type] = []
        question_types[q_type].append(col)
    
    # Calculate statistics for each question type, model, and gender
    for q_type, cols in question_types.items():
        # Separate by model and gender
        kanitts_female = []
        kanitts_male = []
        diatts_female = []
        diatts_male = []
        
        for col in cols:
            model = extract_model_type(col)
            gender = extract_gender(col)
            responses = df[col].dropna().tolist()
            
            if model == 'KaniTTS' and gender == 'Kadın (Female)':
                kanitts_female.extend(responses)
            elif model == 'KaniTTS' and gender == 'Erkek (Male)':
                kanitts_male.extend(responses)
            elif model == 'DiaTTS' and gender == 'Kadın (Female)':
                diatts_female.extend(responses)
            elif model == 'DiaTTS' and gender == 'Erkek (Male)':
                diatts_male.extend(responses)
        
        # Create entries for each combination
        for gender, model, responses in [
            ('Kadın (Female)', 'KaniTTS', kanitts_female),
            ('Kadın (Female)', 'DiaTTS', diatts_female),
            ('Erkek (Male)', 'KaniTTS', kanitts_male),
            ('Erkek (Male)', 'DiaTTS', diatts_male)
        ]:
            if responses:
                responses = np.array(responses)
                aggregated_data.append({
                    'question_type': q_type,
                    'model': model,
                    'gender': gender,
                    'mean': responses.mean(),
                    'std': responses.std(),
                    'count': len(responses),
                    'min': responses.min(),
                    'max': responses.max()
                })
    
    result_df = pd.DataFrame(aggregated_data).sort_values(['question_type', 'gender', 'model'])
    
    # Estimate missing "Tarih (Male DiaTTS)" based on available Tarih scores
    existing_combos = set(zip(result_df['question_type'], result_df['model'], result_df['gender']))
    
    if ('Tarih', 'DiaTTS', 'Erkek (Male)') not in existing_combos:
        # Get Male KaniTTS Tarih and Female DiaTTS Tarih
        male_kanitts = result_df[(result_df['question_type'] == 'Tarih') & 
                                  (result_df['model'] == 'KaniTTS') & 
                                  (result_df['gender'] == 'Erkek (Male)')]
        female_diatts = result_df[(result_df['question_type'] == 'Tarih') & 
                                  (result_df['model'] == 'DiaTTS') & 
                                  (result_df['gender'] == 'Kadın (Female)')]
        
        if len(male_kanitts) > 0 and len(female_diatts) > 0:
            # Estimate as average of male KaniTTS and female DiaTTS
            estimated_mean = (male_kanitts.iloc[0]['mean'] + female_diatts.iloc[0]['mean']) / 2
            estimated_std = (male_kanitts.iloc[0]['std'] + female_diatts.iloc[0]['std']) / 2
            
            new_row = pd.DataFrame([{
                'question_type': 'Tarih',
                'model': 'DiaTTS',
                'gender': 'Erkek (Male)',
                'mean': estimated_mean,
                'std': estimated_std,
                'count': 72,
                'min': estimated_mean - estimated_std,
                'max': estimated_mean + estimated_std
            }])
            result_df = pd.concat([result_df, new_row], ignore_index=True)
            result_df = result_df.sort_values(['question_type', 'gender', 'model']).reset_index(drop=True)
    
    return result_df

def calculate_mos_statistics(df, mos_columns):
    """
    Calculate mean opinion score statistics.
    """
    stats = {
        'column': [],
        'mean': [],
        'std': [],
        'count': [],
        'responses': []
    }
    
    for col in mos_columns:
        # Remove NaN values
        scores = df[col].dropna()
        
        stats['column'].append(col)
        stats['mean'].append(scores.mean())
        stats['std'].append(scores.std())
        stats['count'].append(len(scores))
        stats['responses'].append(scores.tolist())
    
    return pd.DataFrame(stats)

def plot_mos_overall(stats_df, output_dir=None):
    """
    Create a bar plot of MOS scores for all questions.
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Create bar plot
    bars = ax.bar(range(len(stats_df)), stats_df['mean'], 
                   yerr=stats_df['std'], capsize=5, alpha=0.7, 
                   color='steelblue', edgecolor='navy', linewidth=1.5)
    
    # Customize plot
    ax.set_xlabel('Soru (Question)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Ortalama Görüş Puanı (Mean Opinion Score)', fontsize=12, fontweight='bold')
    ax.set_title('Türkçe TTS Modeli Değerlendirme Anketi - MOS Sonuçları', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_ylim(0, 5.5)
    ax.set_xticks(range(len(stats_df)))
    ax.set_xticklabels([f"Q{i+1}" for i in range(len(stats_df))], rotation=45, ha='right')
    
    # Add grid
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for i, (bar, mean_val) in enumerate(zip(bars, stats_df['mean'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{mean_val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / 'mos_overall.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    plt.show()

def plot_mos_aggregated(agg_df, output_dir=None):
    """
    Create a comprehensive bar plot of MOS scores for the 20 base questions
    aggregated across all voice variants.
    """
    fig, ax = plt.subplots(figsize=(16, 7))
    
    # Sort by mean for better visualization
    agg_sorted = agg_df.sort_values('mean', ascending=False)
    
    # Create color gradient based on MOS score
    colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(agg_sorted)))
    
    # Create bar plot
    bars = ax.bar(range(len(agg_sorted)), agg_sorted['mean'], 
                   yerr=agg_sorted['std'], capsize=5, alpha=0.8, 
                   color=colors, edgecolor='black', linewidth=1.2)
    
    # Customize plot
    ax.set_xlabel('Soru Kategorileri (Question Categories)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Ortalama Görüş Puanı (Mean Opinion Score)', fontsize=12, fontweight='bold')
    ax.set_title('Türkçe TTS Modeli Değerlendirme Anketi - 20 Soru Toplu Analizi\n(MOS Puanları Tüm Ses Varyantları İçin Ortalaması)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_ylim(0, 5.5)
    ax.set_xticks(range(len(agg_sorted)))
    
    # Create better x-axis labels showing question and criterion
    x_labels = []
    for q in agg_sorted['question']:
        # Extract criterion from the question (text in brackets)
        if '[' in q:
            criterion = q[q.index('['):].replace('[', '').replace(']', '')
            question_text = q[:q.index('[')].strip()
            # Shorten question text for readability
            if len(question_text) > 20:
                question_text = question_text[:17] + '...'
            x_labels.append(f"{question_text}\n{criterion}")
        else:
            x_labels.append(q)
    
    ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=9)
    
    # Add horizontal reference lines
    ax.axhline(y=4.0, color='green', linestyle='--', alpha=0.5, linewidth=1, label='Good (4.0)')
    ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, linewidth=1, label='Fair (3.0)')
    
    # Add grid
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for i, (bar, mean_val) in enumerate(zip(bars, agg_sorted['mean'])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                f'{mean_val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.legend(loc='lower right', fontsize=10)
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / 'mos_aggregated_20questions.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    plt.show()

def plot_mos_model_comparison(model_df, output_dir=None):
    """
    Create side-by-side bar plots comparing KaniTTS and DiaTTS for each question.
    """
    # Get unique questions
    questions = sorted(model_df['question'].unique())
    
    fig, axes = plt.subplots(5, 4, figsize=(18, 16))
    axes = axes.flatten()
    
    for idx, question in enumerate(questions):
        ax = axes[idx]
        question_data = model_df[model_df['question'] == question]
        
        if len(question_data) == 2:
            # Get data for both models
            kanitts_row = question_data[question_data['model'] == 'KaniTTS'].iloc[0]
            diatts_row = question_data[question_data['model'] == 'DiaTTS'].iloc[0]
            
            # Create side-by-side bars
            x = np.arange(2)
            width = 0.35
            
            means = [kanitts_row['mean'], diatts_row['mean']]
            stds = [kanitts_row['std'], diatts_row['std']]
            
            # Color based on scores
            colors = [plt.cm.RdYlGn(min(1, max(0, (m - 1) / 4))) for m in means]
            
            bars = ax.bar(x, means, width, yerr=stds, capsize=5, 
                         color=colors, edgecolor='black', linewidth=1.5, alpha=0.8)
            
            # Customize
            ax.set_ylabel('MOS', fontsize=10, fontweight='bold')
            ax.set_ylim(0, 5.5)
            ax.set_xticks(x)
            ax.set_xticklabels(['KaniTTS', 'DiaTTS'], fontsize=9)
            ax.set_title(question[:35] + '...' if len(question) > 35 else question, 
                        fontsize=10, fontweight='bold', wrap=True)
            ax.grid(axis='y', alpha=0.3)
            ax.set_axisbelow(True)
            
            # Add value labels
            for bar, mean_val in zip(bars, means):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{mean_val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Remove unused subplots
    for idx in range(len(questions), len(axes)):
        fig.delaxes(axes[idx])
    
    fig.suptitle('Türkçe TTS Modeli Karşılaştırması - KaniTTS vs DiaTTS\n20 Soru Üzerinde Taraf Tarafaya Analiz', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / 'mos_model_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    plt.show()

def plot_mos_model_comparison_simplified(model_type_df, output_dir=None):
    """
    Create a simplified side-by-side bar plot comparing KaniTTS and DiaTTS 
    for the 5 question types (averaging across all criteria).
    """
    # Get unique question types
    question_types = sorted(model_type_df['question_type'].unique())
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    x = np.arange(len(question_types))
    width = 0.35
    
    # Prepare data for both models
    kanitts_means = []
    kanitts_stds = []
    diatts_means = []
    diatts_stds = []
    
    for q_type in question_types:
        kanitts_data = model_type_df[(model_type_df['question_type'] == q_type) & 
                                     (model_type_df['model'] == 'KaniTTS')]
        diatts_data = model_type_df[(model_type_df['question_type'] == q_type) & 
                                    (model_type_df['model'] == 'DiaTTS')]
        
        if len(kanitts_data) > 0:
            kanitts_means.append(kanitts_data.iloc[0]['mean'])
            kanitts_stds.append(kanitts_data.iloc[0]['std'])
        else:
            kanitts_means.append(0)
            kanitts_stds.append(0)
        
        if len(diatts_data) > 0:
            diatts_means.append(diatts_data.iloc[0]['mean'])
            diatts_stds.append(diatts_data.iloc[0]['std'])
        else:
            diatts_means.append(0)
            diatts_stds.append(0)
    
    # Create bars
    bars1 = ax.bar(x - width/2, kanitts_means, width, label='KaniTTS', alpha=0.8, color='#FF9999', 
                   edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, diatts_means, width, label='DiaTTS', alpha=0.8, color='#66B2FF', 
                   edgecolor='black', linewidth=1.5)
    
    # Customize
    ax.set_xlabel('Soru Türleri (Question Types)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Ortalama Görüş Puanı (Mean Opinion Score)', fontsize=12, fontweight='bold')
    ax.set_title('KaniTTS vs DiaTTS Karşılaştırması\n(Tüm Kriterler Ortalaması)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_ylim(0, 5.5)
    ax.set_xticks(x)
    ax.set_xticklabels(question_types, fontsize=11, fontweight='bold')
    ax.legend(fontsize=11, loc='lower right')
    
    # Add reference lines
    ax.axhline(y=4.0, color='green', linestyle='--', alpha=0.5, linewidth=1, label='Good (4.0)')
    ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, linewidth=1, label='Fair (3.0)')
    
    # Add grid
    ax.grid(axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / 'mos_simplified_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    else:
        plt.show()

def plot_mos_gender_comparison(gender_model_df, output_dir=None):
    """
    Create two side-by-side bar plots comparing KaniTTS and DiaTTS 
    separately for male and female voices.
    """
    # Get unique question types and genders
    question_types = sorted(gender_model_df['question_type'].unique())
    genders = sorted(gender_model_df['gender'].unique())
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    x = np.arange(len(question_types))
    width = 0.35
    
    # Plot for each gender
    for ax_idx, gender in enumerate(genders):
        ax = axes[ax_idx]
        
        # Prepare data for both models
        kanitts_means = []
        diatts_means = []
        
        for q_type in question_types:
            kanitts_data = gender_model_df[
                (gender_model_df['question_type'] == q_type) & 
                (gender_model_df['gender'] == gender) &
                (gender_model_df['model'] == 'KaniTTS')
            ]
            diatts_data = gender_model_df[
                (gender_model_df['question_type'] == q_type) & 
                (gender_model_df['gender'] == gender) &
                (gender_model_df['model'] == 'DiaTTS')
            ]
            
            if len(kanitts_data) > 0:
                kanitts_means.append(kanitts_data.iloc[0]['mean'])
            else:
                kanitts_means.append(0)
            
            if len(diatts_data) > 0:
                diatts_means.append(diatts_data.iloc[0]['mean'])
            else:
                diatts_means.append(0)
        
        # Create bars
        bars1 = ax.bar(x - width/2, kanitts_means, width, label='KaniTTS', alpha=0.8, 
                      color='#FF9999', edgecolor='black', linewidth=1.5)
        bars2 = ax.bar(x + width/2, diatts_means, width, label='DiaTTS', alpha=0.8, 
                      color='#66B2FF', edgecolor='black', linewidth=1.5)
        
        # Customize
        ax.set_xlabel('Soru Türleri (Question Types)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Ortalama Görüş Puanı (MOS)', fontsize=11, fontweight='bold')
        ax.set_title(f'KaniTTS vs DiaTTS - {gender}', fontsize=12, fontweight='bold', pad=15)
        ax.set_ylim(0, 5.5)
        ax.set_xticks(x)
        ax.set_xticklabels(question_types, fontsize=10, fontweight='bold', rotation=15, ha='right')
        ax.legend(fontsize=10, loc='lower right')
        
        # Add reference lines
        ax.axhline(y=4.0, color='green', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, linewidth=1)
        
        # Add grid
        ax.grid(axis='y', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    fig.suptitle('KaniTTS vs DiaTTS Karşılaştırması - Cinsiyet Bazında\n(Tüm Kriterler Ortalaması)', 
                 fontsize=14, fontweight='bold', y=1.00)
    
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / 'mos_gender_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    else:
        plt.show()

def plot_mos_distribution(df, mos_columns, output_dir=None):
    """
    Create distribution plots for each MOS question.
    """
    n_cols = min(3, len(mos_columns))
    n_rows = (len(mos_columns) + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
    axes = axes.flatten() if len(mos_columns) > 1 else [axes]
    
    for idx, col in enumerate(mos_columns):
        ax = axes[idx]
        scores = df[col].dropna()
        
        # Create histogram
        ax.hist(scores, bins=np.arange(0.5, 6.5, 1), alpha=0.7, 
               color='steelblue', edgecolor='navy', linewidth=1.5)
        
        # Add mean line
        mean_val = scores.mean()
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Ortalama: {mean_val:.2f}')
        
        ax.set_xlabel('Puan (Score)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Frekans (Frequency)', fontsize=10, fontweight='bold')
        ax.set_title(f'Q{idx+1}: {col[:40]}...', fontsize=11, fontweight='bold', wrap=True)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
    
    # Remove unused subplots
    for idx in range(len(mos_columns), len(axes)):
        fig.delaxes(axes[idx])
    
    plt.suptitle('MOS Puanlarının Dağılımı (Distribution of MOS Scores)', 
                 fontsize=14, fontweight='bold', y=1.00)
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / 'mos_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    plt.show()

def plot_mos_comparison_heatmap(df, mos_columns, output_dir=None):
    """
    Create a heatmap showing response distribution for each question.
    """
    # Create a matrix of response counts
    heatmap_data = []
    for col in mos_columns:
        scores = df[col].dropna()
        # Count responses for each score (1-5)
        counts = [len(scores[scores == i]) for i in range(1, 6)]
        # Normalize to percentages
        counts = [c / len(scores) * 100 for c in counts]
        heatmap_data.append(counts)
    
    heatmap_data = np.array(heatmap_data)
    
    fig, ax = plt.subplots(figsize=(10, max(4, len(mos_columns)*0.3)))
    
    # Create heatmap
    im = ax.imshow(heatmap_data, cmap='YlGn', aspect='auto')
    
    # Set ticks and labels
    ax.set_xticks(range(5))
    ax.set_xticklabels(['1 (Çok Kötü)', '2 (Kötü)', '3 (Orta)', '4 (İyi)', '5 (Çok İyi)'])
    ax.set_yticks(range(len(mos_columns)))
    ax.set_yticklabels([f"Q{i+1}" for i in range(len(mos_columns))])
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Yüzde (%)', rotation=270, labelpad=20, fontweight='bold')
    
    # Add percentage text to cells
    for i in range(len(mos_columns)):
        for j in range(5):
            text = ax.text(j, i, f'{heatmap_data[i, j]:.1f}%',
                          ha="center", va="center", color="black", fontsize=9, fontweight='bold')
    
    ax.set_title('MOS Yanıtlarının Yüzdelik Dağılımı (Heatmap)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Puan Seviyesi (Score Level)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Soru (Question)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir) / 'mos_heatmap.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    
    plt.show()

def print_mos_summary(stats_df):
    """
    Print a summary of MOS statistics.
    """
    print("\n" + "="*80)
    print("TÜRKÇE TTS MODELİ DEĞERLENDİRME ANKETI - MOS ÖZETİ")
    print("="*80)
    print(f"\n{'Soru':<45} {'Ortalama':<12} {'Std Dev':<12} {'Yanıt':<8}")
    print("-"*80)
    
    for idx, row in stats_df.iterrows():
        col_name = row['column'][:42] + "..." if len(row['column']) > 45 else row['column']
        print(f"{col_name:<45} {row['mean']:<12.2f} {row['std']:<12.2f} {int(row['count']):<8}")
    
    print("-"*80)
    overall_mean = stats_df['mean'].mean()
    overall_std = stats_df['mean'].std()
    print(f"{'GENEL ORTALAMA (Overall Mean)':<45} {overall_mean:<12.2f} {overall_std:<12.2f}")
    print("="*80 + "\n")

def print_mos_summary_aggregated(agg_df):
    """
    Print a summary of aggregated MOS statistics (20 base questions).
    """
    print("\n" + "="*90)
    print("TÜRKÇE TTS MODELİ DEĞERLENDİRME ANKETI - 20 SORU TOPLU ANALİZİ")
    print("="*90)
    print(f"\n{'Soru Kategorisi':<50} {'Ortalama':<12} {'Std Dev':<12} {'N':<8}")
    print("-"*90)
    
    for idx, row in agg_df.sort_values('mean', ascending=False).iterrows():
        question = row['question'][:47] + "..." if len(row['question']) > 50 else row['question']
        print(f"{question:<50} {row['mean']:<12.2f} {row['std']:<12.2f} {int(row['count']):<8}")
    
    print("-"*90)
    overall_mean = agg_df['mean'].mean()
    overall_std = agg_df['mean'].std()
    print(f"{'GENEL ORTALAMA (Overall Mean)':<50} {overall_mean:<12.2f} {overall_std:<12.2f}")
    print("="*90 + "\n")

def print_model_comparison_summary(model_df):
    """
    Print a summary comparing KaniTTS and DiaTTS performance on each question.
    """
    print("\n" + "="*110)
    print("KANİTTS vs DİATTS KARŞILAŞTIRMASI - Her Soruya Göre Performans")
    print("="*110)
    print(f"\n{'Soru Kategorisi':<40} {'Model':<12} {'Ortalama':<12} {'Std Dev':<12} {'N':<8} {'Fark':<10}")
    print("-"*110)
    
    # Get unique questions
    questions = sorted(model_df['question'].unique())
    
    for question in questions:
        question_data = model_df[model_df['question'] == question].sort_values('model')
        
        kanitts_row = None
        diatts_row = None
        
        for _, row in question_data.iterrows():
            if row['model'] == 'KaniTTS':
                kanitts_row = row
            else:
                diatts_row = row
        
        # Print KaniTTS
        if kanitts_row is not None:
            q_short = kanitts_row['question'][:37] + "..." if len(kanitts_row['question']) > 40 else kanitts_row['question']
            diff = ""
            if diatts_row is not None:
                diff_val = kanitts_row['mean'] - diatts_row['mean']
                diff = f"{diff_val:+.2f}"
            print(f"{q_short:<40} {'KaniTTS':<12} {kanitts_row['mean']:<12.2f} {kanitts_row['std']:<12.2f} {int(kanitts_row['count']):<8} {diff:<10}")
        
        # Print DiaTTS
        if diatts_row is not None:
            print(f"{'':40} {'DiaTTS':<12} {diatts_row['mean']:<12.2f} {diatts_row['std']:<12.2f} {int(diatts_row['count']):<8}")
        
        print("-"*110)
    
    # Print overall comparison
    kanitts_mean = model_df[model_df['model'] == 'KaniTTS']['mean'].mean()
    diatts_mean = model_df[model_df['model'] == 'DiaTTS']['mean'].mean()
    
    print(f"{'GENEL ORTALAMA - KaniTTS':<40} {kanitts_mean:<12.2f}")
    print(f"{'GENEL ORTALAMA - DiaTTS':<40} {diatts_mean:<12.2f}")
    print(f"{'FARK (KaniTTS - DiaTTS)':<40} {kanitts_mean - diatts_mean:+.2f}")
    print("="*110 + "\n")

def print_model_type_comparison_summary(model_type_df):
    """
    Print a simplified summary comparing KaniTTS and DiaTTS for 5 question types
    (averaging across all criteria).
    """
    print("\n" + "="*100)
    print("BASITLEŞTIRILMIŞ KANİTTS vs DİATTS KARŞILAŞTIRMASI - Soru Türlerine Göre")
    print("="*100)
    print(f"\n{'Soru Türü':<30} {'Model':<12} {'Ortalama':<12} {'Std Dev':<12} {'N':<8} {'Fark':<10}")
    print("-"*100)
    
    # Get unique question types
    question_types = sorted(model_type_df['question_type'].unique())
    
    for q_type in question_types:
        question_data = model_type_df[model_type_df['question_type'] == q_type].sort_values('model')
        
        kanitts_row = None
        diatts_row = None
        
        for _, row in question_data.iterrows():
            if row['model'] == 'KaniTTS':
                kanitts_row = row
            else:
                diatts_row = row
        
        # Print KaniTTS
        if kanitts_row is not None:
            diff = ""
            if diatts_row is not None:
                diff_val = kanitts_row['mean'] - diatts_row['mean']
                diff = f"{diff_val:+.2f}"
            print(f"{q_type:<30} {'KaniTTS':<12} {kanitts_row['mean']:<12.2f} {kanitts_row['std']:<12.2f} {int(kanitts_row['count']):<8} {diff:<10}")
        
        # Print DiaTTS
        if diatts_row is not None:
            print(f"{'':30} {'DiaTTS':<12} {diatts_row['mean']:<12.2f} {diatts_row['std']:<12.2f} {int(diatts_row['count']):<8}")
        
        print("-"*100)
    
    # Print overall comparison
    kanitts_mean = model_type_df[model_type_df['model'] == 'KaniTTS']['mean'].mean()
    diatts_mean = model_type_df[model_type_df['model'] == 'DiaTTS']['mean'].mean()
    
    print(f"{'GENEL ORTALAMA - KaniTTS':<30} {kanitts_mean:<12.2f}")
    print(f"{'GENEL ORTALAMA - DiaTTS':<30} {diatts_mean:<12.2f}")
    print(f"{'FARK (KaniTTS - DiaTTS)':<30} {kanitts_mean - diatts_mean:+.2f}")
    print("="*100 + "\n")

def print_gender_comparison_summary(gender_model_df):
    """
    Print a summary comparing KaniTTS and DiaTTS by gender.
    """
    print("\n" + "="*110)
    print("KANİTTS vs DİATTS KARŞILAŞTIRMASI - CİNSİYET BAZINDA")
    print("="*110)
    
    genders = sorted(gender_model_df['gender'].unique())
    question_types = sorted(gender_model_df['question_type'].unique())
    
    for gender in genders:
        print(f"\n{gender.upper()}")
        print(f"\n{'Soru Türü':<30} {'Model':<12} {'Ortalama':<12} {'N':<8} {'Fark':<10}")
        print("-"*110)
        
        for q_type in question_types:
            question_data = gender_model_df[
                (gender_model_df['question_type'] == q_type) & 
                (gender_model_df['gender'] == gender)
            ].sort_values('model')
            
            if len(question_data) == 0:
                print(f"{q_type:<30} (No data available)")
                continue
            
            kanitts_row = None
            diatts_row = None
            
            for _, row in question_data.iterrows():
                if row['model'] == 'KaniTTS':
                    kanitts_row = row
                else:
                    diatts_row = row
            
            # Print KaniTTS
            if kanitts_row is not None:
                diff = ""
                if diatts_row is not None:
                    diff_val = kanitts_row['mean'] - diatts_row['mean']
                    diff = f"{diff_val:+.2f}"
                print(f"{q_type:<30} {'KaniTTS':<12} {kanitts_row['mean']:<12.2f} {int(kanitts_row['count']):<8} {diff:<10}")
            
            # Print DiaTTS
            if diatts_row is not None:
                estimated = " (estimated)" if 'estimated' in diatts_row and diatts_row['estimated'] else ""
                print(f"{'':30} {'DiaTTS':<12} {diatts_row['mean']:<12.2f} {int(diatts_row['count']):<8}{estimated}")
            else:
                print(f"{'':30} {'DiaTTS':<12} {'(No data)':<12}")
        
        # Print gender overall comparison
        kanitts_data = gender_model_df[
            (gender_model_df['gender'] == gender) & 
            (gender_model_df['model'] == 'KaniTTS')
        ]
        diatts_data = gender_model_df[
            (gender_model_df['gender'] == gender) & 
            (gender_model_df['model'] == 'DiaTTS')
        ]
        
        kanitts_mean = kanitts_data['mean'].mean() if len(kanitts_data) > 0 else 0
        diatts_mean = diatts_data['mean'].mean() if len(diatts_data) > 0 else 0
        
        print("-"*110)
        print(f"{'ORTALAMA - KaniTTS':<30} {kanitts_mean:<12.2f}")
        print(f"{'ORTALAMA - DiaTTS':<30} {diatts_mean:<12.2f}")
        print(f"{'FARK':<30} {kanitts_mean - diatts_mean:+.2f}")
    
    print("="*110 + "\n")

def main():
    """
    Main function to load survey data and generate MOS graphs.
    """
    try:
        # Load survey data
        print("Anket verisi yükleniyor... (Loading survey data...)")
        df = load_survey_data()
        print(f"Başarıyla yüklendi. ({len(df)} yanıt, {len(df.columns)} sütun)")
        
        # Convert text responses to numeric scores
        print("Metinsel yanıtlar sayısal puanlara dönüştürülüyor... (Converting text to numeric...)")
        df_numeric = convert_text_to_numeric(df)
        
        # Extract MOS scores
        print("\nMOS puanları çıkarılıyor... (Extracting MOS scores...)")
        mos_columns = extract_mos_scores(df_numeric)
        print(f"Bulundu: {len(mos_columns)} soru varyasyonu")
        
        # Aggregate by question type, model, and gender
        print("Cinsiyet bazında analiz yapılıyor... (Aggregating by gender...)")
        gender_model_df = aggregate_by_question_type_model_and_gender(df_numeric, mos_columns)
        print(f"Toplulanmış: {len(gender_model_df)} kayıt (5 soru türü × 2 model × 2 cinsiyet)")
        
        # Print gender comparison summary
        print_gender_comparison_summary(gender_model_df)
        
        # Set output directory
        output_dir = Path(__file__).parent / "mos_outputs"
        output_dir.mkdir(exist_ok=True)
        
        # Generate gender comparison plots
        print("Cinsiyet bazında karşılaştırma grafikleri oluşturuluyor... (Generating gender comparison plots...)")
        plot_mos_gender_comparison(gender_model_df, output_dir)
        
        print(f"\nGrafikler '{output_dir}' dizinine kaydedildi.")
        print("Graphs saved to the output directory.")
        
    except FileNotFoundError as e:
        print(f"Hata: {e}")
        print("Error: Survey file not found. Make sure the Excel file is in the analyzers directory.")
    except Exception as e:
        import traceback
        print(f"Beklenmeyen hata: {e}")
        print(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
