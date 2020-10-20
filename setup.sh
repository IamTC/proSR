###################
#  Install conda  #
###################

bit_version=$(uname -m)
conda_installed=$(conda list | grep command)

# if [ "$bit_version" == "x86_64" ] && [ "$conda_installed" != 'command' ]; then
wget -nc https://repo.anaconda.com/miniconda/Miniconda3-3.6.0-Linux-x86_64.sh
chmod +x ./Miniconda3-3.6.0-Linux-x86_64.sh
./Miniconda3-3.6.0-Linux-x86_64.sh -b -f -p /usr/local
# fi

##########################
# Install conda packages #
##########################

conda create -n proSR python=3.6
conda install -y torchvision scikit-image cython
conda install -y pytorch=0.4.1 cuda91 -c pytorch
conda install -y visdom dominate -c conda-forge
python -m pip install easydict pillow

###################
#   Update Path
###################

PROJECT_ROOT=/content/proSR
# if [[! "$PYTHONPATH" == *"$PROJECT_ROOT"* ]]; then
    export PYTHONPATH=/content/proSR/lib:/usr/local/lib/python3.6/site-packages:$PYTHONPATH
# fi

###################
#    Get Data
###################

if [ ! -d $PROJECT_ROOT"/data/checkpoints" ] && [ ! -d $PROJECT_ROOT"/data/datasets" ]; then
    ./data/get_data.sh
fi

# example usage
python test.py -i ./data/datasets/B100/LR_bicubic/X2/38092x2.png -o ~/Pictures/proSR/ --checkpoint $PROJECT_ROOT/data/checkpoints/proSRGAN_x8.pth --scale 8 --cpu