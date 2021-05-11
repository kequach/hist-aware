python bert/run_pretraining.py \
    --bert_config_file /home/leonardovida/dev/hist-aware/notebooks/models/delphbert/config/bert_config.json \
    --input_file "/home/leonardovida/data/volume_1/data-histaware/pretraining-data-cased/tf_*.tfrecord" \
    --vocab_file /home/leonardovida/data/volume_1/data-histaware/tokenizer/1970/dutch.bert.vocab_mod.128.cased \
    --output_dir /home/leonardovida/data/volume_1/data-histaware/pretraining_output \
    --max_seq_length 128 \
    --max_predictions_per_seq 15 \
    --do_train True \
    --train_batch_size 2 \
    --learning_rate 1e-4
    
    
    --num_train_steps=1000000 \
    --iterations_per_loop=10000 \
    --num_warmup_steps=10000 \
    --save_checkpoints_steps=10000 \
    --max_eval_steps=10000