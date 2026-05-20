import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import urllib.request
import urllib.parse
import os

# --- Page Configuration ---
st.set_page_config(page_title="Bulk QR Generator Suite", page_icon="🔲", layout="wide")

# --- Font Download Helper for Labels ---
@st.cache_resource
def get_font(size):
    font_path = "Roboto-Bold.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception as e:
            return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

st.title("🔲 Bulk QR Code Generator Suite")
st.markdown("Switch between the tabs below depending on the type of QR code you need to generate today.")

# --- Create Tabs ---
tab1, tab2 = st.tabs(["🏷️ Dual-QR Bin Labels (100x25mm)", "📲 UPI Payment QRs (A4 Print)"])

# ==========================================
# TAB 1: DUAL-QR THERMAL LABELS (From PDF)
# ==========================================
with tab1:
    st.header("Dual-QR Thermal Label Generator")
    st.markdown("Generate 100x25mm labels at 300 DPI for ZDesigner thermal printers.")
    
    col_settings, col_preview = st.columns([1, 1.2])

    with col_settings:
        st.markdown("### 1. Input Data")
        default_label_input = "CHL-A05D3\nCHL-A05D2\nCHL-A05D1"
        raw_text_labels = st.text_area("Paste your IDs from PDF/Excel:", height=200, value=default_label_input, key="label_input")
        raw_ids_labels = [line.replace('"', '').strip() for line in raw_text_labels.split('\n') if line.strip()]

        st.markdown("### 2. Label Dimensions")
        c1, c2, c3 = st.columns(3)
        width_mm = c1.number_input("Width (mm)", value=100.0, step=1.0)
        height_mm = c2.number_input("Height (mm)", value=25.0, step=1.0)
        dpi = c3.number_input("DPI", value=300, step=50)

        st.markdown("### 3. Design Fine-Tuning")
        qr_scale = st.slider("QR Code Size (%)", min_value=50, max_value=100, value=85) / 100.0
        qr_margin_x = st.slider("Left Margin (px)", min_value=0, max_value=200, value=50)
        qr_spacing = st.slider("Space Between QRs (px)", min_value=0, max_value=100, value=30)
        font_size = st.slider("Font Size", min_value=20, max_value=150, value=75)
        text_x_offset = st.slider("Text Position (px from left)", min_value=200, max_value=1000, value=630)

    # Label Logic
    def generate_label(data_string, w_mm, h_mm, dpi_val, q_scale, q_mar_x, q_space, f_size, t_offset):
        width_px = int((w_mm / 25.4) * dpi_val)
        height_px = int((h_mm / 25.4) * dpi_val)
        img = Image.new('RGB', (width_px, height_px), 'white')
        draw = ImageDraw.Draw(img)

        qr = qrcode.QRCode(version=1, box_size=10, border=0)
        qr.add_data(data_string)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").get_image()

        qr_size = int(height_px * q_scale)
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        y_pos = (height_px - qr_size) // 2

        qr1_x = q_mar_x
        img.paste(qr_img, (qr1_x, y_pos))
        qr2_x = qr1_x + qr_size + q_space
        img.paste(qr_img, (qr2_x, y_pos))

        font = get_font(f_size)
        bbox = draw.textbbox((0, 0), data_string, font=font)
        text_h = bbox[3] - bbox[1]
        text_y = (height_px - text_h) // 2 - bbox[1]
        
        draw.text((t_offset, text_y), data_string, fill="black", font=font)
        return img

    with col_preview:
        st.markdown("### 🔍 Live Preview")
        if len(raw_ids_labels) > 0:
            preview_img = generate_label(raw_ids_labels[0], width_mm, height_mm, dpi, qr_scale, qr_margin_x, qr_spacing, font_size, text_x_offset)
            # Updated to width="stretch"
            st.image(preview_img, width="stretch", caption=f"Preview: {raw_ids_labels[0]}")
            
            st.markdown("---")
            # Updated to width="stretch"
            if st.button("📦 Generate Bulk Labels PDF", type="primary", width="stretch"):
                progress_bar = st.progress(0, text="Generating PDF...")
                pdf_buffer = io.BytesIO()
                
                images = []
                for i, uid in enumerate(raw_ids_labels):
                    img = generate_label(uid, width_mm, height_mm, dpi, qr_scale, qr_margin_x, qr_spacing, font_size, text_x_offset)
                    images.append(img.convert('RGB'))
                    progress_bar.progress((i + 1) / len(raw_ids_labels), text=f"Processing {i+1} of {len(raw_ids_labels)}...")
                
                if images:
                    images[0].save(
                        pdf_buffer, 
                        format="PDF", 
                        resolution=dpi, 
                        save_all=True, 
                        append_images=images[1:]
                    )
                
                progress_bar.empty()
                st.success("✅ Labels PDF generated successfully!")
                # Updated to width="stretch"
                st.download_button("Download Print-Ready PDF", data=pdf_buffer.getvalue(), file_name="Dual_QR_Labels.pdf", mime="application/pdf", width="stretch")
        else:
            st.warning("Please paste at least one ID.")


# ==========================================
# TAB 2: UPI PAYMENT QRs (Original Setup)
# ==========================================
with tab2:
    st.header("UPI Payment QR Generator")
    st.markdown("Generate simple, high-resolution (300 DPI) square QR codes for A4 layout printing.")
    
    col_upi_1, col_upi_2 = st.columns(2)
    with col_upi_1:
        default_upi_input = "Paytmqr65ec57@ptys\n7877993040@okbizaxis"
        raw_text_upi = st.text_area("Paste your UPI IDs (One per line):", height=200, value=default_upi_input, key="upi_input")
        raw_ids_upi = [line.strip() for line in raw_text_upi.split('\n') if line.strip()]

    with col_upi_2:
        add_upi_prefix = st.checkbox("Format as Scannable Payment Link", value=True, help="Adds 'upi://pay?pa=' to the ID.")
        payee_name = st.text_input("Default Payee Name (Optional):", value="", help="Adds &pn=Name to the QR code.")
        
        # Updated to width="stretch"
        if st.button("🚀 Generate UPI QRs PDF", type="primary", width="stretch"):
            if not raw_ids_upi:
                st.error("Please enter at least one UPI ID.")
            else:
                pdf_buffer_upi = io.BytesIO()
                prog_upi = st.progress(0, text="Generating QRs...")
                
                images_upi = []
                for i, uid in enumerate(raw_ids_upi):
                    qr_data = f"upi://pay?pa={uid}&pn={urllib.parse.quote(payee_name)}" if add_upi_prefix and payee_name else (f"upi://pay?pa={uid}" if add_upi_prefix else uid)
                    
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=25, border=4)
                    qr.add_data(qr_data)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white").get_image()
                    images_upi.append(img.convert('RGB'))
                    
                    prog_upi.progress((i + 1) / len(raw_ids_upi))
                    
                if images_upi:
                    images_upi[0].save(
                        pdf_buffer_upi, 
                        format="PDF", 
                        resolution=300, 
                        save_all=True, 
                        append_images=images_upi[1:]
                    )
                        
                prog_upi.empty()
                st.success(f"✅ Generated PDF with {len(raw_ids_upi)} UPI QR codes!")
                # Updated to width="stretch"
                st.download_button("📦 Download UPI QRs PDF", data=pdf_buffer_upi.getvalue(), file_name="Bulk_UPI_QRCodes.pdf", mime="application/pdf", width="stretch")
